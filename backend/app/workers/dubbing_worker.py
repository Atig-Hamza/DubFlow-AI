import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, Set
from fastapi import WebSocket
from backend.app.core.database import SessionLocal
from backend.app.core.logging import logger, app_logger
from backend.app.models.project import Project
from backend.app.models.speaker import Speaker
from backend.app.models.transcript import TranscriptLine
from backend.app.models.job import Job
from backend.app.services.video_service import video_service
from backend.app.services.audio_service import audio_service
from backend.app.services.asr_service import asr_service
from backend.app.services.diarization_service import diarization_service
from backend.app.services.speaker_service import speaker_service
from backend.app.services.translation_service import translation_service
from backend.app.services.tts_service import tts_service
from backend.app.services.synchronization_service import synchronization_service
from backend.app.services.mixing_service import mixing_service
from backend.app.services.rendering_service import rendering_service
from backend.app.utils.gpu import clean_vram

class JobBroadcaster:
    """
    Manages active WebSocket subscriptions to broadcast real-time job progress and logs.
    """
    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        if job_id not in self._connections:
            self._connections[job_id] = set()
        self._connections[job_id].add(websocket)

    def disconnect(self, job_id: str, websocket: WebSocket):
        if job_id in self._connections:
            self._connections[job_id].discard(websocket)
            if not self._connections[job_id]:
                del self._connections[job_id]

    async def broadcast(self, job_id: str, data: Dict[str, Any]):
        if job_id in self._connections:
            dead_sockets = set()
            for ws in self._connections[job_id]:
                try:
                    await ws.send_json(data)
                except Exception:
                    dead_sockets.add(ws)
            for ws in dead_sockets:
                self._connections[job_id].discard(ws)

job_broadcaster = JobBroadcaster()

class DubbingWorker:
    def __init__(self):
        pass

    async def update_job(
        self,
        job_id: str,
        stage: str,
        progress: int,
        log_message: Optional[str] = None,
        status: str = "processing",
        error: Optional[str] = None
    ):
        db = SessionLocal()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.current_stage = stage
                job.progress_percent = progress
                job.status = status
                if error:
                    job.error_message = error
                if log_message:
                    job.add_log(stage, log_message)
                if status in ["completed", "failed", "cancelled"]:
                    job.completed_at = datetime.utcnow()
                db.commit()

                # Broadcast update
                payload = job.to_dict()
                await job_broadcaster.broadcast(job_id, payload)
        finally:
            db.close()

    async def run_analyze_pipeline(self, project_id: str, job_id: str):
        """
        Phase 1 & Phase 2 Pipeline:
        Extract Audio -> ASR Transcription -> Speaker Diarization -> Speaker Profiles -> Initial Translation
        """
        logger.info(f"[JOB: {job_id}] Initiating Analysis Pipeline for project {project_id}...")
        db = SessionLocal()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ValueError(f"Project not found: {project_id}")

            video_path = project.original_video_path
            target_lang = project.target_language or "French"
            source_lang = project.source_language or "English"

            # 1. Inspect Video
            await self.update_job(job_id, "Extracting audio", 10, "Extracting video audio streams...")
            video_info = video_service.inspect_video(video_path)

            project.duration = video_info["duration"]
            project.width = video_info["width"]
            project.height = video_info["height"]
            project.fps = video_info["fps"]
            db.commit()

            # 2. Extract Audio
            audio_16k = await audio_service.extract_audio_from_video(video_path, project_id)
            master_stereo = await audio_service.extract_master_stereo_audio(video_path, project_id)

            project.extracted_audio_path = audio_16k
            db.commit()

            # 3. Transcribe Audio (ASR)
            await self.update_job(job_id, "Transcribing", 30, f"Transcribing dialogue with Whisper ASR...")
            asr_segments = await asr_service.transcribe_audio(audio_16k, language=source_lang)
            await self.update_job(job_id, "Transcribing", 50, f"Identified {len(asr_segments)} speech lines.")

            # 4. Speaker Diarization
            await self.update_job(job_id, "Detecting speakers", 60, "Running acoustic diarization clustering...")
            transcript_dicts = [s.to_dict() for s in asr_segments]
            diarization_result = await diarization_service.diarize_audio(audio_16k, transcript_dicts)
            
            num_speakers = diarization_result["num_speakers"]
            await self.update_job(job_id, "Detecting speakers", 75, f"Detected {num_speakers} distinct speaker(s).")

            # 5. Align Transcript with Speakers
            aligned_lines = diarization_service.align_transcript_with_speakers(
                asr_segments,
                diarization_result["segment_assignments"]
            )

            # 6. Create Speaker Profiles
            await self.update_job(job_id, "Creating speaker profiles", 80, "Building voice profiles & acoustic metrics...")
            profiles = await speaker_service.create_speaker_profiles(
                project_id=project_id,
                target_language=target_lang,
                aligned_lines=aligned_lines,
                audio_path=audio_16k
            )

            # Clear any old speakers/lines if re-analyzing
            db.query(Speaker).filter(Speaker.project_id == project_id).delete()
            db.query(TranscriptLine).filter(TranscriptLine.project_id == project_id).delete()

            # Save speakers
            speakers_map = {}
            for prof in profiles:
                spk = Speaker(
                    project_id=project_id,
                    speaker_tag=prof["speaker_tag"],
                    display_name=prof["display_name"],
                    segments_count=prof["segments_count"],
                    total_speech_time=prof["total_speech_time"],
                    avg_pitch=prof["avg_pitch"],
                    speaking_rate=prof["speaking_rate"],
                    loudness=prof["loudness"],
                    gender_detected=prof["gender_detected"],
                    confidence=prof["confidence"],
                    sample_audio_path=prof["sample_audio_path"],
                    assigned_voice_id=prof["assigned_voice_id"],
                    voice_consent=True
                )
                db.add(spk)
                speakers_map[prof["speaker_tag"]] = spk

            # Save transcript lines
            db_lines = []
            for line in aligned_lines:
                t_line = TranscriptLine(
                    project_id=project_id,
                    speaker_id=line["speaker"],
                    start=line["start"],
                    end=line["end"],
                    original_text=line["text"],
                    confidence=line["confidence"],
                    translation="",
                    status="ready"
                )
                db.add(t_line)
                db_lines.append(t_line)

            project.speakers_count = len(profiles)
            project.status = "analyzed"
            db.commit()

            # 7. Initial Contextual Translation with NVIDIA API
            await self.update_job(job_id, "Translating", 88, f"Translating dialogue into {target_lang} via NVIDIA API...")
            
            lines_data = [l.to_dict() for l in db_lines]
            
            translated_data = await translation_service.translate_project_transcript(
                lines=lines_data,
                source_lang=source_lang,
                target_lang=target_lang,
                speakers_map=speakers_map
            )

            # Update lines with translated text
            for i, l_db in enumerate(db_lines):
                l_db.translation = translated_data[i]["translation"]
                l_db.status = "ready"
            
            db.commit()
            clean_vram()
            await self.update_job(job_id, "Completed", 100, "Analysis and initial translation complete!", status="completed")

        except Exception as e:
            logger.error(f"[JOB: {job_id}] Analysis failed: {e}", exc_info=True)
            await self.update_job(job_id, "Failed", 0, f"Error: {str(e)}", status="failed", error=str(e))
            try:
                project = db.query(Project).filter(Project.id == project_id).first()
                if project:
                    project.status = "failed"
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

    async def run_dubbing_pipeline(self, project_id: str, job_id: str):
        """
        Phases 3-6 Pipeline:
        TTS Voice Generation -> Timing Synchronization -> Audio Mixing (Vocals + SFX/Music) -> Final Video Rendering
        """
        logger.info(f"[JOB: {job_id}] Starting Dubbing Pipeline for project {project_id}...")
        db = SessionLocal()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ValueError(f"Project {project_id} not found")

            project.status = "dubbing"
            db.commit()

            speakers = {s.speaker_tag: s for s in project.speakers}
            transcript_lines = db.query(TranscriptLine).filter(TranscriptLine.project_id == project_id).order_by(TranscriptLine.start).all()
            
            total_duration = project.duration
            video_path = project.original_video_path
            master_stereo = str(project.extracted_audio_path).replace("_16k_mono.wav", "_master_stereo.wav")
            suppression_val = project.voice_suppression if project.voice_suppression is not None else 1.0
            music_val = project.music_volume if project.music_volume is not None else 0.85
            dialogue_val = project.dialogue_volume if project.dialogue_volume is not None else 1.0

            # 1. Voice Generation (TTS)
            total_lines = len(transcript_lines)
            await self.update_job(job_id, "Generating voices", 15, f"Synthesizing {total_lines} dialogue lines...")

            for idx, line in enumerate(transcript_lines):
                spk = speakers.get(line.speaker_id)
                voice_id = spk.assigned_voice_id if spk and spk.assigned_voice_id else "fr-FR-HenriNeural"
                text_to_speak = line.translation if (line.translation and line.translation.strip()) else line.original_text

                # Synthesize line
                raw_audio = await tts_service.generate_line_audio(
                    project_id=project_id,
                    line_id=line.id,
                    text=text_to_speak,
                    voice_id=voice_id
                )

                line.generated_audio_path = raw_audio
                db.commit()

                current_pct = 15 + int((idx + 1) / max(total_lines, 1) * 25)
                await self.update_job(job_id, "Generating voices", current_pct, f"Generated voice for line {idx+1}/{total_lines}")

            # 2. Timing Synchronization
            await self.update_job(job_id, "Synchronizing voices", 45, "Synchronizing dialogue timing and durations...")
            
            synced_lines_info = []
            for idx, line in enumerate(transcript_lines):
                next_start = transcript_lines[idx + 1].start if (idx + 1) < len(transcript_lines) else None
                sync_result = await synchronization_service.synchronize_line_audio(
                    raw_audio_path=line.generated_audio_path,
                    project_id=project_id,
                    line_id=line.id,
                    target_start=line.start,
                    target_end=line.end,
                    next_start=next_start,
                    max_duration=total_duration
                )
                line.synchronized_audio_path = sync_result["synced_path"]
                line.time_stretch_ratio = sync_result["ratio"]
                line.status = "dubbed"
                db.commit()

                synced_lines_info.append({
                    "id": line.id,
                    "start": line.start,
                    "end": line.end,
                    "dubbed_end": line.start + sync_result.get("final_duration", line.end - line.start),
                    "synchronized_audio_path": sync_result["synced_path"]
                })

            await self.update_job(job_id, "Synchronizing voices", 65, "All dialogue lines synchronized.")

            # 3. Audio Mixing (Background Music/SFX + Dubbed Dialogue)
            await self.update_job(job_id, "Mixing audio", 70, "Separating soundtrack and assembling dialogue stems...")

            speech_intervals = [{"start": l["start"], "end": max(l["end"], l.get("dubbed_end", l["end"]))} for l in synced_lines_info]
            
            # Create background bed with original vocal suppression
            bg_track = await mixing_service.create_background_track(
                master_audio_path=master_stereo,
                project_id=project_id,
                speech_intervals=speech_intervals,
                total_duration=total_duration,
                voice_suppression=suppression_val,
                music_volume=music_val
            )

            # Assemble dubbed dialogue track
            dialogue_track = await mixing_service.assemble_dialogue_track(
                synced_lines=synced_lines_info,
                project_id=project_id,
                total_duration=total_duration,
                dialogue_volume=dialogue_val
            )

            # Final audio mix
            final_audio_mix = await mixing_service.mix_audio(bg_track, dialogue_track, project_id)

            project.separated_background_path = bg_track
            project.separated_vocals_path = dialogue_track
            db.commit()

            await self.update_job(job_id, "Mixing audio", 85, "Soundtrack and dialogue mixed cleanly.")

            # 4. Final Video Rendering
            await self.update_job(job_id, "Rendering video", 90, "Reconstructing dubbed video container...")
            final_video = await rendering_service.render_dubbed_video(
                video_path=video_path,
                audio_path=final_audio_mix,
                project_id=project_id
            )

            project.final_video_path = final_video
            project.status = "completed"
            db.commit()

            clean_vram()
            await self.update_job(job_id, "Completed", 100, "Dubbed video rendered successfully!", status="completed")

        except Exception as e:
            logger.error(f"[JOB: {job_id}] Dubbing failed: {e}", exc_info=True)
            await self.update_job(job_id, "Failed", 0, f"Error: {str(e)}", status="failed", error=str(e))
            try:
                project = db.query(Project).filter(Project.id == project_id).first()
                if project:
                    project.status = "failed"
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

    async def run_regenerate_line(self, project_id: str, line_id: str, new_translation: Optional[str] = None):
        """
        Regenerates TTS and synchronization for an individual dialogue line.
        """
        db = SessionLocal()
        try:
            line = db.query(TranscriptLine).filter(TranscriptLine.id == line_id).first()
            if not line:
                raise ValueError(f"Line {line_id} not found")

            project = db.query(Project).filter(Project.id == project_id).first()
            speaker = db.query(Speaker).filter(Speaker.project_id == project_id, Speaker.speaker_tag == line.speaker_id).first()

            if new_translation:
                line.translation = new_translation

            voice_id = speaker.assigned_voice_id if speaker and speaker.assigned_voice_id else "fr-FR-HenriNeural"
            text_to_speak = line.translation if line.translation else line.original_text

            raw_audio = await tts_service.generate_line_audio(
                project_id=project_id,
                line_id=line.id,
                text=text_to_speak,
                voice_id=voice_id
            )
            line.generated_audio_path = raw_audio

            sync_res = await synchronization_service.synchronize_line_audio(
                raw_audio_path=raw_audio,
                project_id=project_id,
                line_id=line.id,
                target_start=line.start,
                target_end=line.end
            )
            line.synchronized_audio_path = sync_res["synced_path"]
            line.time_stretch_ratio = sync_res["ratio"]
            line.status = "dubbed"
            db.commit()
            return line.to_dict()
        finally:
            db.close()

dubbing_worker = DubbingWorker()
