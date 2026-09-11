import os
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import librosa
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
from scipy.spatial.distance import cdist
from backend.app.core.logging import logger

class SpeakerSegment:
    def __init__(self, start: float, end: float, speaker_id: str, confidence: float = 0.90):
        self.start = start
        self.end = end
        self.speaker_id = speaker_id
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "speaker": self.speaker_id,
            "start": round(self.start, 2),
            "end": round(self.end, 2),
            "confidence": round(self.confidence, 2)
        }

class LocalDiarizationProvider:
    """
    Automatic Speaker Diarization and Voice Profiling Engine.
    Extracts acoustic feature embeddings, automatically determines the number of speakers,
    clusters segments, and creates distinct speaker profiles.
    """
    def __init__(self):
        pass

    def extract_acoustic_embedding(self, y_segment: np.ndarray, sr: int) -> np.ndarray:
        """
        Extracts a 108-dimensional normalized acoustic speaker embedding:
        - 20 MFCCs (mean + std) -> 40 dims
        - Delta MFCCs (mean + std) -> 40 dims
        - Spectral Centroid, Rolloff, Bandwidth, Contrast -> 14 dims
        - Chroma & Pitch features -> 14 dims
        """
        if len(y_segment) < sr * 0.15:  # Too short
            y_segment = np.pad(y_segment, (0, int(sr * 0.2) - len(y_segment)), mode="wrap")

        # 1. MFCCs
        mfcc = librosa.feature.mfcc(y=y_segment, sr=sr, n_mfcc=20)
        mfcc_mean = np.mean(mfcc, axis=1)
        mfcc_std = np.std(mfcc, axis=1)

        # 2. Delta MFCCs
        mfcc_delta = librosa.feature.delta(mfcc)
        delta_mean = np.mean(mfcc_delta, axis=1)
        delta_std = np.std(mfcc_delta, axis=1)

        # 3. Spectral features
        centroid = np.mean(librosa.feature.spectral_centroid(y=y_segment, sr=sr))
        rolloff = np.mean(librosa.feature.spectral_rolloff(y=y_segment, sr=sr))
        bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=y_segment, sr=sr))
        contrast = np.mean(librosa.feature.spectral_contrast(y=y_segment, sr=sr), axis=1)

        # 4. Chroma & Zero-Crossing
        chroma = np.mean(librosa.feature.chroma_stft(y=y_segment, sr=sr), axis=1)
        zcr = np.mean(librosa.feature.zero_crossing_rate(y_segment))

        features = np.hstack([
            mfcc_mean,
            mfcc_std,
            delta_mean,
            delta_std,
            [centroid, rolloff, bandwidth, zcr],
            contrast,
            chroma[:10]  # first 10 chroma
        ])

        # L2 normalize
        norm = np.linalg.norm(features)
        if norm > 1e-6:
            features = features / norm
        return features

    def diarize(self, audio_path: str, transcript_segments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Performs automatic speaker diarization on audio:
        1. Segments audio based on speech intervals or provided transcript boundaries.
        2. Computes speaker embeddings for each segment.
        3. Automatically determines optimal number of speakers via Silhouette analysis.
        4. Clusters segments and assigns speaker IDs (speaker_01, speaker_02, etc.).
        5. Computes speaker profiles and centroids.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"[DIARIZATION] Loading audio for diarization: {audio_path}")
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        total_duration = len(y) / sr

        # Determine intervals to analyze
        intervals: List[Tuple[float, float]] = []
        if transcript_segments and len(transcript_segments) > 0:
            for seg in transcript_segments:
                s = max(0.0, float(seg.get("start", 0.0)))
                e = min(total_duration, float(seg.get("end", total_duration)))
                if e - s >= 0.25:
                    intervals.append((s, e))
        else:
            # Automatic Voice Activity Detection using librosa.effects.split
            splits = librosa.effects.split(y, top_db=25, frame_length=1024, hop_length=256)
            for start_idx, end_idx in splits:
                s = start_idx / sr
                e = end_idx / sr
                if e - s >= 0.35:
                    intervals.append((s, e))

        if not intervals:
            # Fallback if no intervals found
            intervals = [(0.0, total_duration)]

        # Extract embeddings for each interval
        embeddings = []
        valid_intervals = []
        for s, e in intervals:
            s_idx = int(s * sr)
            e_idx = int(e * sr)
            clip = y[s_idx:e_idx]
            if len(clip) >= sr * 0.15:
                emb = self.extract_acoustic_embedding(clip, sr)
                embeddings.append(emb)
                valid_intervals.append((s, e))

        num_segments = len(embeddings)
        logger.info(f"[DIARIZATION] Extracted embeddings for {num_segments} speech segments.")

        if num_segments == 0:
            return {
                "num_speakers": 1,
                "speakers": [{"id": "speaker_01", "segments": [(0.0, total_duration)]}],
                "segment_assignments": [{"start": 0.0, "end": total_duration, "speaker": "speaker_01", "confidence": 0.9}]
            }

        # Convert to numpy matrix
        X = np.array(embeddings)

        # Automatically determine optimal speaker count (1 to min(6, num_segments))
        optimal_k = 1
        labels = np.zeros(num_segments, dtype=int)

        if num_segments == 2:
            sim = float(np.dot(X[0], X[1]))
            logger.info(f"[DIARIZATION] 2 segments cosine similarity: {sim:.3f}")
            if sim < 0.88:
                optimal_k = 2
                labels = np.array([0, 1], dtype=int)
        elif num_segments >= 3:
            max_candidates = min(5, num_segments - 1)
            best_score = -1.0
            
            for k in range(2, max_candidates + 1):
                try:
                    clusterer = AgglomerativeClustering(n_clusters=k, metric="cosine", linkage="average")
                    cluster_labels = clusterer.fit_predict(X)
                    
                    # Compute silhouette score with cosine metric
                    score = silhouette_score(X, cluster_labels, metric="cosine")
                    logger.debug(f"[DIARIZATION] Candidate k={k} -> Silhouette score: {score:.3f}")
                    
                    # Clear threshold for multi-speaker detection
                    if score > 0.25 and score > best_score:
                        best_score = score
                        optimal_k = k
                        labels = cluster_labels
                except Exception as ce:
                    logger.debug(f"[DIARIZATION] Clustering k={k} evaluation skipped: {ce}")

        logger.info(f"[DIARIZATION] Automatically determined {optimal_k} speaker(s).")

        # Formulate speaker clusters
        speakers_dict: Dict[str, List[Tuple[float, float]]] = {}
        speaker_centroids: Dict[str, np.ndarray] = {}

        for i, (s, e) in enumerate(valid_intervals):
            spk_num = labels[i] + 1
            spk_id = f"speaker_{spk_num:02d}"
            if spk_id not in speakers_dict:
                speakers_dict[spk_id] = []
            speakers_dict[spk_id].append((s, e))

        # Calculate speaker centroids & profiles
        for spk_id in sorted(speakers_dict.keys()):
            spk_idx = int(spk_id.split("_")[1]) - 1
            spk_indices = np.where(labels == spk_idx)[0]
            if len(spk_indices) > 0:
                centroid = np.mean(X[spk_indices], axis=0)
                norm = np.linalg.norm(centroid)
                if norm > 0:
                    centroid = centroid / norm
                speaker_centroids[spk_id] = centroid

        # Compile segment assignments with confidence
        assigned_segments: List[Dict[str, Any]] = []
        for i, (s, e) in enumerate(valid_intervals):
            spk_num = labels[i] + 1
            spk_id = f"speaker_{spk_num:02d}"
            # Confidence based on cosine distance to centroid
            centroid = speaker_centroids.get(spk_id)
            if centroid is not None:
                sim = float(np.dot(X[i], centroid))
                conf = max(0.70, min(0.98, (sim + 1.0) / 2.0))
            else:
                conf = 0.90

            assigned_segments.append({
                "start": round(s, 2),
                "end": round(e, 2),
                "speaker": spk_id,
                "confidence": round(conf, 2)
            })

        formatted_speakers = []
        for spk_id in sorted(speakers_dict.keys()):
            formatted_speakers.append({
                "id": spk_id,
                "segments": [{"start": round(s, 2), "end": round(e, 2)} for s, e in speakers_dict[spk_id]],
                "centroid": speaker_centroids.get(spk_id).tolist() if speaker_centroids.get(spk_id) is not None else []
            })

        return {
            "num_speakers": len(formatted_speakers),
            "speakers": formatted_speakers,
            "segment_assignments": assigned_segments
        }
