/**
 * DubFlow AI — Frontend Client Controller
 */

// Application State
const state = {
    currentProject: null,
    projects: [],
    languages: [],
    selectedFile: null,
    activeJobId: null,
    socket: null,
    pollingInterval: null,
    audioPlayer: new Audio(),
    voiceBrowserSpeakerId: null,
    voiceBrowserCurrentVoiceId: null,
    allVoices: [],
    voiceFilters: { gender: 'all', dialect: 'all', search: '' },
    previewAudioPlayer: new Audio()
};

// DOM Elements
const el = {
    // Nav & Modals
    projectSelector: document.getElementById('project-selector'),
    btnNewProject: document.getElementById('btn-new-project'),
    btnOpenDiagnostics: document.getElementById('btn-open-diagnostics'),
    modalDiagnostics: document.getElementById('modal-diagnostics'),
    btnCloseDiagnostics: document.getElementById('btn-close-diagnostics'),
    btnRunDiagnostics: document.getElementById('btn-run-diagnostic-test'),
    diagnosticsList: document.getElementById('diagnostics-list'),

    // Upload Section
    sectionUpload: document.getElementById('section-upload'),
    dropZone: document.getElementById('drop-zone'),
    videoFileInput: document.getElementById('video-file-input'),
    selectedFileDisplay: document.getElementById('selected-file-display'),
    selectedFilename: document.getElementById('selected-filename'),
    selectedFilesize: document.getElementById('selected-filesize'),
    targetLangSelect: document.getElementById('target-language-select'),
    sourceLangSelect: document.getElementById('source-language-select'),
    btnUploadAnalyze: document.getElementById('btn-upload-analyze'),

    // Project View Section
    sectionProjectView: document.getElementById('section-project-view'),
    currentProjectName: document.getElementById('current-project-name'),
    projectStatusBadge: document.getElementById('project-status-badge'),
    mainVideoPlayer: document.getElementById('main-video-player'),
    statSpeakersPill: document.getElementById('stat-speakers-pill'),
    statDuration: document.getElementById('stat-duration'),
    statResolution: document.getElementById('stat-resolution'),
    statSourceLang: document.getElementById('stat-source-lang'),
    statTargetLang: document.getElementById('stat-target-lang'),

    // Sliders
    sliderDialogueVol: document.getElementById('slider-dialogue-vol'),
    sliderMusicVol: document.getElementById('slider-music-vol'),
    sliderSuppression: document.getElementById('slider-suppression'),
    valDialogueVol: document.getElementById('val-dialogue-vol'),
    valMusicVol: document.getElementById('val-music-vol'),
    valSuppression: document.getElementById('val-suppression'),

    // Actions
    btnStartDubbing: document.getElementById('btn-start-dubbing'),
    btnReanalyze: document.getElementById('btn-reanalyze'),

    // Stepper & Progress
    processingCard: document.getElementById('processing-card'),
    processingStageLabel: document.getElementById('processing-stage-label'),
    processingPercent: document.getElementById('processing-percent'),
    processingProgressBar: document.getElementById('processing-progress-bar'),
    logStreamContainer: document.getElementById('log-stream-container'),
    logCount: document.getElementById('log-count'),

    // Speakers & Transcript
    speakersList: document.getElementById('speakers-list'),
    transcriptTableBody: document.getElementById('transcript-table-body'),
    btnSaveTranscript: document.getElementById('btn-save-transcript'),

    // Rename Modal
    modalSpeakerRename: document.getElementById('modal-speaker-rename'),
    renameSpeakerId: document.getElementById('rename-speaker-id'),
    renameSpeakerInput: document.getElementById('rename-speaker-input'),
    btnSaveSpeakerName: document.getElementById('btn-save-speaker-name'),

    // Output
    outputCard: document.getElementById('output-card'),
    compareOriginalVideo: document.getElementById('compare-original-video'),
    compareDubbedVideo: document.getElementById('compare-dubbed-video'),
    btnDownloadVideo: document.getElementById('btn-download-video'),

    // Voice Browser Modal (50+ Voices)
    modalVoiceBrowser: document.getElementById('modal-voice-browser'),
    voiceBrowserGrid: document.getElementById('voice-browser-grid'),
    voiceBrowserCountPill: document.getElementById('voice-browser-count-pill'),
    voiceSearchInput: document.getElementById('voice-search-input'),
    voiceDialectFilter: document.getElementById('voice-dialect-filter'),
    voiceBrowserStatus: document.getElementById('voice-browser-status'),
};

// ----------------------------------------------------
// Initialization
// ----------------------------------------------------
document.addEventListener('DOMContentLoaded', async () => {
    setupEventListeners();
    await loadLanguages();
    await loadRecentProjects();
});

function setupEventListeners() {
    // File Drop & Selection
    el.dropZone.addEventListener('click', () => el.videoFileInput.click());
    el.videoFileInput.addEventListener('change', handleFileSelect);

    el.dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        el.dropZone.classList.add('border-indigo-400', 'bg-slate-900/80');
    });
    el.dropZone.addEventListener('dragleave', () => {
        el.dropZone.classList.remove('border-indigo-400', 'bg-slate-900/80');
    });
    el.dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        el.dropZone.classList.remove('border-indigo-400', 'bg-slate-900/80');
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    // Upload & Analyze Trigger
    el.btnUploadAnalyze.addEventListener('click', startUploadAndAnalyze);

    // Dubbing & Reanalyze Triggers
    el.btnStartDubbing.addEventListener('click', startDubbingPipeline);
    el.btnReanalyze.addEventListener('click', () => {
        if (state.currentProject) triggerAnalyzeJob(state.currentProject.id);
    });

    // Audio mixing sliders
    el.sliderDialogueVol.addEventListener('input', (e) => {
        el.valDialogueVol.textContent = Math.round(e.target.value * 100) + '%';
    });
    el.sliderMusicVol.addEventListener('input', (e) => {
        el.valMusicVol.textContent = Math.round(e.target.value * 100) + '%';
    });
    el.sliderSuppression.addEventListener('input', (e) => {
        el.valSuppression.textContent = Math.round(e.target.value * 100) + '%';
    });

    // Transcript save
    el.btnSaveTranscript.addEventListener('click', saveTranscriptEdits);

    // Diagnostics Modal
    el.btnOpenDiagnostics.addEventListener('click', () => {
        el.modalDiagnostics.classList.remove('hidden');
        runDiagnosticsTest();
    });
    el.btnCloseDiagnostics.addEventListener('click', () => el.modalDiagnostics.classList.add('hidden'));
    el.btnRunDiagnostics.addEventListener('click', runDiagnosticsTest);

    // Project Switcher
    el.projectSelector.addEventListener('change', (e) => {
        if (e.target.value) loadProject(e.target.value);
    });
    el.btnNewProject.addEventListener('click', () => {
        state.currentProject = null;
        state.selectedFile = null;
        el.selectedFileDisplay.classList.add('hidden');
        el.sectionProjectView.classList.add('hidden');
        el.sectionUpload.classList.remove('hidden');
        el.projectSelector.value = '';
    });

    // Speaker Rename Modal
    el.btnSaveSpeakerName.addEventListener('click', saveSpeakerRename);

    // Voice Browser Filter Event Listeners
    document.querySelectorAll('.voice-gender-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.voice-gender-btn').forEach(b => {
                b.className = 'voice-gender-btn px-3 py-1 rounded-md text-xs font-medium text-gray-400 hover:text-white transition';
            });
            btn.className = 'voice-gender-btn px-3 py-1 rounded-md text-xs font-semibold bg-indigo-600 text-white transition';
            state.voiceFilters.gender = btn.dataset.gender;
            renderVoiceBrowserGrid();
        });
    });

    if (el.voiceDialectFilter) {
        el.voiceDialectFilter.addEventListener('change', (e) => {
            state.voiceFilters.dialect = e.target.value;
            renderVoiceBrowserGrid();
        });
    }

    if (el.voiceSearchInput) {
        el.voiceSearchInput.addEventListener('input', (e) => {
            state.voiceFilters.search = e.target.value;
            renderVoiceBrowserGrid();
        });
    }
}

// ----------------------------------------------------
// File Handling
// ----------------------------------------------------
function handleFileSelect(e) {
    if (e.target.files && e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
}

function handleFile(file) {
    state.selectedFile = file;
    el.selectedFilename.textContent = file.name;
    const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
    el.selectedFilesize.textContent = `(${sizeMb} MB)`;
    el.selectedFileDisplay.classList.remove('hidden');
}

// ----------------------------------------------------
// API Calls: Languages & Projects
// ----------------------------------------------------
async function loadLanguages() {
    try {
        const res = await fetch('/api/languages');
        state.languages = await res.json();
    } catch (err) {
        console.error('Failed to load languages:', err);
    }
}

async function loadRecentProjects() {
    try {
        const res = await fetch('/api/projects');
        state.projects = await res.json();
        
        el.projectSelector.innerHTML = '<option value="">Select Project...</option>';
        state.projects.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = `${p.name} (${p.target_language})`;
            el.projectSelector.appendChild(opt);
        });
    } catch (err) {
        console.error('Failed to load projects:', err);
    }
}

// ----------------------------------------------------
// Project Lifecycle: Upload -> Analyze
// ----------------------------------------------------
async function startUploadAndAnalyze() {
    if (!state.selectedFile) {
        alert('Please select or drop a video file first.');
        return;
    }

    el.btnUploadAnalyze.disabled = true;
    el.btnUploadAnalyze.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i><span>Uploading Video...</span>`;
    lucide.createIcons();

    try {
        const targetLang = el.targetLangSelect.value;
        const sourceLang = el.sourceLangSelect.value;

        // 1. Create project
        const createRes = await fetch('/api/projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: state.selectedFile.name.replace(/\.[^/.]+$/, ""),
                source_language: sourceLang,
                target_language: targetLang
            })
        });
        const project = await createRes.json();

        // 2. Upload video file
        const formData = new FormData();
        formData.append('file', state.selectedFile);
        formData.append('target_language', targetLang);
        formData.append('source_language', sourceLang);

        const uploadRes = await fetch(`/api/projects/${project.id}/upload`, {
            method: 'POST',
            body: formData
        });
        const uploadedProject = await uploadRes.json();

        // 3. Switch to Project View
        await loadProject(uploadedProject.id);

        // 4. Trigger Analysis
        await triggerAnalyzeJob(uploadedProject.id);

    } catch (err) {
        console.error('Upload failed:', err);
        alert('Upload failed: ' + err.message);
    } finally {
        el.btnUploadAnalyze.disabled = false;
        el.btnUploadAnalyze.innerHTML = `<i data-lucide="sparkles" class="w-4 h-4"></i><span>Upload & Analyze Video</span>`;
        lucide.createIcons();
    }
}

async function triggerAnalyzeJob(projectId) {
    try {
        showProcessingCard('Starting video analysis...');
        resetStepperChecklist();
        updateStepperStep('step-upload', 'completed');

        const res = await fetch(`/api/projects/${projectId}/analyze`, { method: 'POST' });
        const data = await res.json();
        
        subscribeToJob(data.job_id, () => {
            loadProject(projectId);
        });
    } catch (err) {
        console.error('Failed to trigger analysis:', err);
        hideProcessingCard();
    }
}

// ----------------------------------------------------
// Project Lifecycle: Dubbing
// ----------------------------------------------------
async function startDubbingPipeline() {
    if (!state.currentProject) return;

    el.btnStartDubbing.disabled = true;
    showProcessingCard('Starting Dubbing Pipeline...');
    resetStepperChecklist();
    updateStepperStep('step-upload', 'completed');
    updateStepperStep('step-extract', 'completed');
    updateStepperStep('step-diarization', 'completed');
    updateStepperStep('step-transcribe', 'completed');

    try {
        const body = {
            dialogue_volume: parseFloat(el.sliderDialogueVol.value),
            music_volume: parseFloat(el.sliderMusicVol.value),
            voice_suppression: parseFloat(el.sliderSuppression.value)
        };

        const res = await fetch(`/api/projects/${state.currentProject.id}/dub`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await res.json();

        subscribeToJob(data.job_id, () => {
            loadProject(state.currentProject.id);
        });
    } catch (err) {
        console.error('Failed to start dubbing:', err);
        alert('Dubbing error: ' + err.message);
        hideProcessingCard();
    } finally {
        el.btnStartDubbing.disabled = false;
    }
}

// ----------------------------------------------------
// Job Tracking: WebSocket & Polling Fallback
// ----------------------------------------------------
function subscribeToJob(jobId, onComplete) {
    state.activeJobId = jobId;

    if (state.socket) {
        state.socket.close();
    }
    if (state.pollingInterval) {
        clearInterval(state.pollingInterval);
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/jobs/${jobId}`;

    try {
        state.socket = new WebSocket(wsUrl);

        state.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleJobUpdate(data, onComplete);
        };

        state.socket.onerror = () => {
            startPolling(jobId, onComplete);
        };
    } catch (e) {
        startPolling(jobId, onComplete);
    }
}

function startPolling(jobId, onComplete) {
    state.pollingInterval = setInterval(async () => {
        try {
            const res = await fetch(`/api/jobs/${jobId}`);
            if (res.ok) {
                const data = await res.json();
                handleJobUpdate(data, onComplete);
            }
        } catch (e) {
            console.warn('Polling error:', e);
        }
    }, 1500);
}

function handleJobUpdate(data, onComplete) {
    const stage = data.current_stage || 'Processing';
    const percent = data.progress || 0;

    el.processingStageLabel.textContent = stage;
    el.processingPercent.textContent = `${percent}%`;
    el.processingProgressBar.style.width = `${percent}%`;

    // Map stages to checklist icons
    updateStepperFromStage(stage, percent);

    // Update log stream
    if (data.logs && data.logs.length > 0) {
        el.logCount.textContent = `${data.logs.length} events`;
        el.logStreamContainer.innerHTML = data.logs.map(log => `
            <div class="flex items-start space-x-2">
                <span class="text-indigo-400 shrink-0">[${log.timestamp}]</span>
                <span class="text-violet-300 font-semibold shrink-0">[${log.stage}]</span>
                <span class="text-gray-300">${escapeHtml(log.message)}</span>
            </div>
        `).join('');
        el.logStreamContainer.scrollTop = el.logStreamContainer.scrollHeight;
    }

    if (data.status === 'completed') {
        if (state.socket) state.socket.close();
        if (state.pollingInterval) clearInterval(state.pollingInterval);
        
        setTimeout(() => {
            hideProcessingCard();
            if (onComplete) onComplete();
        }, 1200);
    } else if (data.status === 'failed') {
        if (state.socket) state.socket.close();
        if (state.pollingInterval) clearInterval(state.pollingInterval);
        alert('Job failed: ' + (data.error || 'Unknown error'));
        hideProcessingCard();
    }
}

function updateStepperFromStage(stage, percent) {
    const stageLower = stage.toLowerCase();
    if (stageLower.includes('extract')) {
        updateStepperStep('step-upload', 'completed');
        updateStepperStep('step-extract', 'active');
    } else if (stageLower.includes('transcrib')) {
        updateStepperStep('step-extract', 'completed');
        updateStepperStep('step-transcribe', 'active');
    } else if (stageLower.includes('speaker') || stageLower.includes('diariz')) {
        updateStepperStep('step-transcribe', 'completed');
        updateStepperStep('step-diarization', 'active');
    } else if (stageLower.includes('profile')) {
        updateStepperStep('step-diarization', 'completed');
    } else if (stageLower.includes('translat')) {
        updateStepperStep('step-diarization', 'completed');
        updateStepperStep('step-translate', 'active');
    } else if (stageLower.includes('voice') || stageLower.includes('tts')) {
        updateStepperStep('step-translate', 'completed');
        updateStepperStep('step-tts', 'active');
    } else if (stageLower.includes('sync')) {
        updateStepperStep('step-tts', 'completed');
        updateStepperStep('step-sync', 'active');
    } else if (stageLower.includes('mix')) {
        updateStepperStep('step-sync', 'completed');
        updateStepperStep('step-mix', 'active');
    } else if (stageLower.includes('render')) {
        updateStepperStep('step-mix', 'completed');
        updateStepperStep('step-render', 'active');
    } else if (stageLower.includes('complet')) {
        ['step-upload', 'step-extract', 'step-diarization', 'step-transcribe', 'step-translate', 'step-tts', 'step-sync', 'step-mix', 'step-render', 'step-complete'].forEach(s => updateStepperStep(s, 'completed'));
    }
}

function updateStepperStep(stepId, status) {
    const item = document.getElementById(stepId);
    if (!item) return;
    const icon = item.querySelector('.step-icon');
    if (status === 'completed') {
        item.className = 'p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center space-x-2 text-emerald-300';
        icon.textContent = '✓';
        icon.className = 'step-icon text-emerald-400 font-bold';
    } else if (status === 'active') {
        item.className = 'p-2.5 rounded-lg bg-indigo-500/20 border border-indigo-500/40 flex items-center space-x-2 text-indigo-200 animate-pulse';
        icon.textContent = '●';
        icon.className = 'step-icon text-indigo-400 font-bold';
    } else {
        item.className = 'p-2.5 rounded-lg bg-slate-800/50 border border-white/5 flex items-center space-x-2 text-gray-300';
        icon.textContent = '○';
        icon.className = 'step-icon text-gray-500';
    }
}

function resetStepperChecklist() {
    ['step-upload', 'step-extract', 'step-diarization', 'step-transcribe', 'step-translate', 'step-tts', 'step-sync', 'step-mix', 'step-render', 'step-complete'].forEach(s => updateStepperStep(s, 'waiting'));
}

function showProcessingCard(msg) {
    el.processingCard.classList.remove('hidden');
    el.processingStageLabel.textContent = msg;
    el.processingCard.scrollIntoView({ behavior: 'smooth' });
}

function hideProcessingCard() {
    el.processingCard.classList.add('hidden');
}

// ----------------------------------------------------
// Load Project State & Render Views
// ----------------------------------------------------
async function loadProject(projectId) {
    try {
        const res = await fetch(`/api/projects/${projectId}`);
        if (!res.ok) throw new Error('Failed to load project');
        
        const project = await res.json();
        state.currentProject = project;

        // Switch visible sections
        el.sectionUpload.classList.add('hidden');
        el.sectionProjectView.classList.remove('hidden');
        el.projectSelector.value = project.id;

        // Set Header details
        el.currentProjectName.textContent = project.name;
        el.projectStatusBadge.textContent = project.status.toUpperCase();
        
        // Metadata stats
        el.statDuration.textContent = formatTime(project.duration);
        el.statResolution.textContent = `${project.width}x${project.height} (${project.fps}fps)`;
        el.statSourceLang.textContent = project.source_language || 'English';
        el.statTargetLang.textContent = project.target_language || 'French';
        el.statSpeakersPill.textContent = `${project.speakers_count || 0} Speakers Detected`;

        // Video Player Source
        if (project.original_video_path) {
            const filename = project.original_video_path.split(/[\\/]/).pop();
            el.mainVideoPlayer.src = `/api/media/uploads/${filename}`;
            el.compareOriginalVideo.src = `/api/media/uploads/${filename}`;
        }

        // Output section if completed
        if (project.final_video_path) {
            const outFilename = project.final_video_path.split(/[\\/]/).pop();
            el.outputCard.classList.remove('hidden');
            el.compareDubbedVideo.src = `/api/media/outputs/${outFilename}`;
            el.btnDownloadVideo.href = `/api/projects/${project.id}/output`;
        } else {
            el.outputCard.classList.add('hidden');
        }

        // Render Speakers
        renderSpeakers(project.speakers || [], project.target_language);

        // Render Transcript
        renderTranscript(project.transcript || []);

        lucide.createIcons();
    } catch (err) {
        console.error('Error loading project:', err);
    }
}

// ----------------------------------------------------
// Speaker Management (Section 17)
// ----------------------------------------------------
function renderSpeakers(speakers, targetLang) {
    if (!speakers || speakers.length === 0) {
        el.speakersList.innerHTML = `
            <div class="col-span-full py-8 text-center text-xs text-gray-400 bg-slate-900/40 rounded-xl border border-white/5">
                <i data-lucide="users" class="w-8 h-8 mx-auto text-gray-500 mb-2"></i>
                No speakers analyzed yet. Click "Analyze Video" to detect speakers.
            </div>
        `;
        return;
    }

    const currentLangMeta = state.languages.find(l => l.name.toLowerCase() === (targetLang || 'french').toLowerCase()) || state.languages[0];
    const availableVoices = currentLangMeta ? currentLangMeta.voices : [];

    el.speakersList.innerHTML = speakers.map(spk => {
        const sampleUrl = spk.sample_audio_path ? `/api/media/voices/${spk.sample_audio_path.split(/[\\/]/).pop()}` : '';
        return `
            <div class="bg-slate-900/60 rounded-xl p-4 border border-white/10 space-y-3 relative group hover:border-violet-500/40 transition">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2">
                        <div class="w-7 h-7 rounded-lg bg-violet-500/20 text-violet-400 flex items-center justify-center font-bold text-xs font-mono">
                            ${spk.speaker_tag.replace('speaker_', 'S')}
                        </div>
                        <div>
                            <span class="font-bold text-sm text-gray-100">${escapeHtml(spk.display_name)}</span>
                            <span class="block text-[10px] text-gray-400">${spk.speaker_tag}</span>
                        </div>
                    </div>
                    <button onclick="openSpeakerRename('${spk.id}', '${escapeHtml(spk.display_name)}')" class="text-xs text-gray-400 hover:text-white p-1 rounded hover:bg-white/5 transition" title="Rename Speaker">
                        <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
                    </button>
                </div>

                <!-- Acoustic Characteristics Specs -->
                <div class="grid grid-cols-2 gap-2 text-[11px] bg-slate-950/60 p-2.5 rounded-lg border border-white/5">
                    <div>
                        <span class="text-gray-400 block text-[10px]">Speech Duration</span>
                        <span class="font-mono text-gray-200 font-semibold">${formatTime(spk.total_speech_time)} (${spk.segments_count} lines)</span>
                    </div>
                    <div>
                        <span class="text-gray-400 block text-[10px]">Confidence</span>
                        <span class="font-mono text-emerald-400 font-semibold">${spk.confidence}%</span>
                    </div>
                    <div>
                        <span class="text-gray-400 block text-[10px]">Pitch / Timbre</span>
                        <span class="font-mono text-violet-300 font-semibold">${spk.avg_pitch} Hz (${spk.gender_detected})</span>
                    </div>
                    <div>
                        <span class="text-gray-400 block text-[10px]">Speaking Pace</span>
                        <span class="font-mono text-cyan-300 font-semibold">${spk.speaking_rate} wpm</span>
                    </div>
                </div>

                <!-- Voice Selection & Preview -->
                <div class="space-y-1.5 pt-1">
                    <div class="flex items-center justify-between">
                        <label class="block text-[11px] text-gray-400 font-medium">Assigned AI Voice</label>
                        <button onclick="openVoiceBrowser('${spk.id}', '${spk.assigned_voice_id}')" class="text-[11px] text-indigo-400 hover:text-indigo-300 font-semibold flex items-center space-x-1 transition hover:underline">
                            <i data-lucide="sparkles" class="w-3 h-3"></i>
                            <span>Browse 50+ Voices</span>
                        </button>
                    </div>
                    <div class="flex items-center space-x-2">
                        <select onchange="changeSpeakerVoice('${spk.id}', this.value)" class="glass-input flex-1 rounded-lg px-2.5 py-1.5 text-xs text-gray-200">
                            ${availableVoices.map(v => `
                                <option value="${v.id}" ${v.id === spk.assigned_voice_id ? 'selected' : ''}>${v.name}</option>
                            `).join('')}
                        </select>
                        <button onclick="playVoicePreview('${spk.id}')" class="px-2.5 py-1.5 rounded-lg bg-violet-600/20 hover:bg-violet-600/30 text-violet-300 border border-violet-500/30 text-xs transition flex items-center space-x-1" title="Preview Voice">
                            <i data-lucide="volume-2" class="w-3.5 h-3.5"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function openSpeakerRename(speakerId, currentName) {
    el.renameSpeakerId.value = speakerId;
    el.renameSpeakerInput.value = currentName;
    el.modalSpeakerRename.classList.remove('hidden');
    el.renameSpeakerInput.focus();
}

async function saveSpeakerRename() {
    const speakerId = el.renameSpeakerId.value;
    const newName = el.renameSpeakerInput.value.trim();
    if (!newName || !state.currentProject) return;

    try {
        await fetch(`/api/projects/${state.currentProject.id}/speakers/${speakerId}/voice`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ display_name: newName })
        });
        el.modalSpeakerRename.classList.add('hidden');
        await loadProject(state.currentProject.id);
    } catch (err) {
        alert('Failed to rename speaker: ' + err.message);
    }
}

async function changeSpeakerVoice(speakerId, voiceId) {
    if (!state.currentProject) return;
    try {
        await fetch(`/api/projects/${state.currentProject.id}/speakers/${speakerId}/voice`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ assigned_voice_id: voiceId })
        });
        console.log(`Speaker ${speakerId} voice changed to ${voiceId}`);
    } catch (err) {
        alert('Failed to update voice: ' + err.message);
    }
}

function playVoicePreview(speakerId) {
    if (!state.currentProject) return;
    state.audioPlayer.src = `/api/projects/${state.currentProject.id}/speakers/${speakerId}/preview?t=${Date.now()}`;
    state.audioPlayer.play().catch(e => console.warn('Audio play error:', e));
}

// ----------------------------------------------------
// Transcript Management (Section 18)
// ----------------------------------------------------
function renderTranscript(lines) {
    if (!lines || lines.length === 0) {
        el.transcriptTableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-8 text-gray-500 italic">No dialogue lines transcribed yet.</td>
            </tr>
        `;
        return;
    }

    el.transcriptTableBody.innerHTML = lines.map(line => {
        const hasAudio = !!line.synchronized_audio_path;
        return `
            <tr data-line-id="${line.id}" class="hover:bg-white/[0.02] transition">
                <!-- Speaker -->
                <td class="py-3 px-4 font-mono">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        ${line.speaker_id}
                    </span>
                </td>

                <!-- Timestamps -->
                <td class="py-3 px-4 font-mono text-[11px] text-gray-400">
                    ${formatTime(line.start, false)} → ${formatTime(line.end, false)}
                </td>

                <!-- Original Dialogue -->
                <td class="py-3 px-4 text-gray-300">
                    <p class="leading-relaxed">${escapeHtml(line.original)}</p>
                    <span class="text-[10px] text-gray-500 font-mono">Conf: ${line.confidence}%</span>
                </td>

                <!-- Editable Translation -->
                <td class="py-3 px-4">
                    <textarea class="transcript-translation-input glass-input w-full rounded-lg px-2.5 py-1.5 text-xs text-indigo-200 resize-none h-14" data-id="${line.id}">${escapeHtml(line.translation || '')}</textarea>
                </td>

                <!-- Status -->
                <td class="py-3 px-4 text-center">
                    <span class="px-2 py-0.5 rounded text-[10px] font-semibold ${line.status === 'dubbed' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-700/50 text-gray-400'}">
                        ${line.status}
                    </span>
                </td>

                <!-- Actions -->
                <td class="py-3 px-4 text-right space-x-1.5 whitespace-nowrap">
                    ${hasAudio ? `
                        <button onclick="playLineAudio('${line.synchronized_audio_path}')" class="p-1.5 rounded-lg bg-violet-600/20 hover:bg-violet-600/30 text-violet-300 border border-violet-500/30 transition" title="Listen to dubbed audio">
                            <i data-lucide="play" class="w-3.5 h-3.5"></i>
                        </button>
                    ` : ''}
                    <button onclick="regenerateLine('${line.id}')" class="p-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 transition" title="Regenerate this line">
                        <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

async function saveTranscriptEdits() {
    if (!state.currentProject) return;

    const textareas = document.querySelectorAll('.transcript-translation-input');
    const updates = [];
    textareas.forEach(ta => {
        updates.push({
            id: ta.getAttribute('data-id'),
            translation: ta.value
        });
    });

    try {
        el.btnSaveTranscript.innerHTML = `<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i><span>Saving...</span>`;
        lucide.createIcons();

        await fetch(`/api/projects/${state.currentProject.id}/transcript`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lines: updates })
        });

        alert('Transcript edits saved successfully!');
    } catch (err) {
        alert('Failed to save transcript: ' + err.message);
    } finally {
        el.btnSaveTranscript.innerHTML = `<i data-lucide="save" class="w-3.5 h-3.5"></i><span>Save Edits</span>`;
        lucide.createIcons();
    }
}

function playLineAudio(audioPath) {
    const filename = audioPath.split(/[\\/]/).pop();
    state.audioPlayer.src = `/api/media/segments/${filename}?t=${Date.now()}`;
    state.audioPlayer.play().catch(e => console.warn('Audio play error:', e));
}

async function regenerateLine(lineId) {
    if (!state.currentProject) return;
    const textarea = document.querySelector(`.transcript-translation-input[data-id="${lineId}"]`);
    const newTranslation = textarea ? textarea.value : null;

    try {
        const res = await fetch(`/api/projects/${state.currentProject.id}/lines/${lineId}/regenerate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ translation: newTranslation })
        });
        const data = await res.json();
        
        // Play the newly regenerated line audio immediately!
        if (data.line && data.line.synchronized_audio_path) {
            playLineAudio(data.line.synchronized_audio_path);
        }
        await loadProject(state.currentProject.id);
    } catch (err) {
        alert('Regenerate failed: ' + err.message);
    }
}

// ----------------------------------------------------
// Diagnostics System (Section 27)
// ----------------------------------------------------
async function runDiagnosticsTest() {
    el.diagnosticsList.innerHTML = `
        <div class="text-center py-6 text-xs text-gray-400">
            <i data-lucide="loader-2" class="w-6 h-6 mx-auto mb-2 text-indigo-400 animate-spin"></i>
            Testing FFmpeg, PyTorch, CUDA, NVIDIA APIs, and AI models...
        </div>
    `;
    lucide.createIcons();

    try {
        const res = await fetch('/api/diagnostics/test');
        const data = await res.json();
        const diag = data.diagnostics;

        el.diagnosticsList.innerHTML = Object.keys(diag).map(key => {
            const item = diag[key];
            let badgeClass = 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20';
            if (item.status === 'missing' || item.status === 'error') {
                badgeClass = 'bg-red-500/10 text-red-300 border-red-500/20';
            } else if (item.status.includes('required') || item.status.includes('unavailable')) {
                badgeClass = 'bg-amber-500/10 text-amber-300 border-amber-500/20';
            }

            return `
                <div class="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-white/5 text-xs">
                    <div class="space-y-0.5">
                        <span class="font-bold text-gray-200 block">${escapeHtml(item.name)}</span>
                        <span class="text-gray-400 text-[11px]">${escapeHtml(item.details)}</span>
                    </div>
                    <span class="px-2.5 py-1 rounded-lg border text-[11px] font-semibold ${badgeClass}">
                        ${item.badge}
                    </span>
                </div>
            `;
        }).join('');
        lucide.createIcons();
    } catch (err) {
        el.diagnosticsList.innerHTML = `
            <div class="text-center py-4 text-xs text-red-400">
                Failed to run system test: ${escapeHtml(err.message)}
            </div>
        `;
    }
}

// ----------------------------------------------------
// Helpers
// ----------------------------------------------------
function formatTime(seconds, includeMs = false) {
    if (!seconds || seconds < 0) seconds = 0;
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    if (includeMs) {
        const ms = Math.floor((seconds - Math.floor(seconds)) * 100);
        return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${String(ms).padStart(2, '0')}`;
    }
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// ----------------------------------------------------
// Voice Browser Modal & Filtering (50+ Neural Voices)
// ----------------------------------------------------
async function openVoiceBrowser(speakerId, currentVoiceId) {
    state.voiceBrowserSpeakerId = speakerId;
    state.voiceBrowserCurrentVoiceId = currentVoiceId;
    el.modalVoiceBrowser.classList.remove('hidden');
    el.voiceSearchInput.value = '';
    state.voiceFilters = { gender: 'all', dialect: 'all', search: '' };
    
    // Reset gender buttons UI
    document.querySelectorAll('.voice-gender-btn').forEach(btn => {
        if (btn.dataset.gender === 'all') {
            btn.className = 'voice-gender-btn px-3 py-1 rounded-md text-xs font-semibold bg-indigo-600 text-white transition';
        } else {
            btn.className = 'voice-gender-btn px-3 py-1 rounded-md text-xs font-medium text-gray-400 hover:text-white transition';
        }
    });

    el.voiceBrowserGrid.innerHTML = `
        <div class="col-span-full py-12 text-center text-xs text-gray-400">
            <i data-lucide="loader-2" class="w-6 h-6 mx-auto mb-2 text-indigo-400 animate-spin"></i>
            Loading studio voice catalog...
        </div>
    `;
    lucide.createIcons();

    try {
        const lang = state.currentProject ? state.currentProject.target_language : 'Arabic';
        const res = await fetch(`/api/voices?language=${encodeURIComponent(lang)}`);
        const data = await res.json();
        state.allVoices = data.voices || [];

        // Extract unique dialects/regions for dropdown
        const regions = new Set();
        state.allVoices.forEach(v => {
            if (v.country && v.country !== 'Global') regions.add(v.country);
        });

        el.voiceDialectFilter.innerHTML = `<option value="all">All Regions & Dialects</option>` +
            Array.from(regions).sort().map(r => `<option value="${escapeHtml(r)}">${escapeHtml(r)}</option>`).join('');

        renderVoiceBrowserGrid();
    } catch (err) {
        console.error('Failed to load voices:', err);
        el.voiceBrowserGrid.innerHTML = `
            <div class="col-span-full py-12 text-center text-xs text-red-400">
                Failed to load voices: ${escapeHtml(err.message)}
            </div>
        `;
    }
}

function closeVoiceBrowser() {
    el.modalVoiceBrowser.classList.add('hidden');
    if (state.previewAudioPlayer) {
        state.previewAudioPlayer.pause();
    }
}

function renderVoiceBrowserGrid() {
    let filtered = state.allVoices;

    // Filter by gender
    if (state.voiceFilters.gender !== 'all') {
        filtered = filtered.filter(v => (v.gender || '').toLowerCase() === state.voiceFilters.gender.toLowerCase());
    }

    // Filter by dialect/region
    if (state.voiceFilters.dialect !== 'all') {
        filtered = filtered.filter(v => (v.country || '').toLowerCase() === state.voiceFilters.dialect.toLowerCase());
    }

    // Filter by search text
    if (state.voiceFilters.search.trim()) {
        const q = state.voiceFilters.search.trim().toLowerCase();
        filtered = filtered.filter(v => {
            const corpus = `${v.id} ${v.name} ${v.country || ''} ${v.dialect || ''} ${v.style || ''}`.toLowerCase();
            return corpus.includes(q);
        });
    }

    el.voiceBrowserCountPill.textContent = `${filtered.length} Voices Available`;

    if (filtered.length === 0) {
        el.voiceBrowserGrid.innerHTML = `
            <div class="col-span-full py-12 text-center text-xs text-gray-400">
                <i data-lucide="search-x" class="w-8 h-8 mx-auto text-gray-500 mb-2"></i>
                No voices match your filters. Try clearing search or selecting "All".
            </div>
        `;
        lucide.createIcons();
        return;
    }

    el.voiceBrowserGrid.innerHTML = filtered.map(v => {
        const isSelected = v.id === state.voiceBrowserCurrentVoiceId;
        const isMale = (v.gender || '').toLowerCase() === 'male';
        const genderBadgeClass = isMale ? 'bg-sky-500/10 text-sky-300 border-sky-500/20' : 'bg-pink-500/10 text-pink-300 border-pink-500/20';
        const genderIcon = isMale ? '👨' : '👩';

        return `
            <div class="p-3.5 rounded-xl border ${isSelected ? 'border-indigo-500 bg-indigo-950/40 shadow-lg shadow-indigo-500/10' : 'border-white/10 bg-slate-900/70 hover:border-white/20'} space-y-2.5 transition flex flex-col justify-between">
                <div>
                    <div class="flex items-start justify-between gap-2">
                        <div class="flex items-center space-x-2">
                            <span class="text-base">${v.flag || '🎙️'}</span>
                            <div>
                                <h4 class="text-xs font-bold text-gray-100 flex items-center space-x-1.5">
                                    <span>${escapeHtml(v.name)}</span>
                                    ${isSelected ? '<span class="text-[10px] px-1.5 py-0.2 rounded bg-indigo-500 text-white font-semibold">Active</span>' : ''}
                                </h4>
                                <span class="text-[10px] text-gray-400 font-mono">${v.id}</span>
                            </div>
                        </div>
                        <span class="px-2 py-0.5 rounded text-[10px] font-semibold border ${genderBadgeClass}">
                            ${genderIcon} ${escapeHtml(v.gender)}
                        </span>
                    </div>

                    <div class="flex flex-wrap items-center gap-1.5 pt-2 text-[10px]">
                        <span class="px-2 py-0.5 rounded bg-slate-800 text-gray-300 border border-white/5">
                            📍 ${escapeHtml(v.country || 'Standard')}
                        </span>
                        <span class="px-2 py-0.5 rounded bg-slate-800 text-violet-300 border border-white/5">
                            ✨ ${escapeHtml(v.style || 'Studio')}
                        </span>
                    </div>
                </div>

                <div class="flex items-center justify-between gap-2 pt-2 border-t border-white/5">
                    <button type="button" onclick="playVoiceDirectPreview('${v.id}')" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-gray-200 border border-white/5 transition flex items-center space-x-1.5">
                        <i data-lucide="play" class="w-3 h-3 text-indigo-400"></i>
                        <span>Preview</span>
                    </button>
                    <button type="button" onclick="selectVoiceForSpeaker('${v.id}')" class="px-3.5 py-1.5 rounded-lg ${isSelected ? 'bg-indigo-600 text-white' : 'bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-md shadow-indigo-600/20'} text-xs font-semibold transition flex items-center space-x-1">
                        <i data-lucide="check" class="w-3 h-3"></i>
                        <span>${isSelected ? 'Selected' : 'Use Voice'}</span>
                    </button>
                </div>
            </div>
        `;
    }).join('');

    lucide.createIcons();
}

function playVoiceDirectPreview(voiceId) {
    if (state.previewAudioPlayer) {
        state.previewAudioPlayer.pause();
    }
    el.voiceBrowserStatus.textContent = `Streaming preview for ${voiceId}...`;
    state.previewAudioPlayer.src = `/api/voices/${voiceId}/preview?t=${Date.now()}`;
    state.previewAudioPlayer.play().then(() => {
        el.voiceBrowserStatus.textContent = `Playing preview: ${voiceId}`;
    }).catch(err => {
        console.error('Preview error:', err);
        el.voiceBrowserStatus.textContent = `Preview error: ${err.message}`;
    });
    state.previewAudioPlayer.onended = () => {
        el.voiceBrowserStatus.textContent = 'Preview finished. Click preview on any voice to listen.';
    };
}

async function selectVoiceForSpeaker(voiceId) {
    if (!state.currentProject || !state.voiceBrowserSpeakerId) return;
    try {
        await changeSpeakerVoice(state.voiceBrowserSpeakerId, voiceId);
        closeVoiceBrowser();
        await loadProject(state.currentProject.id);
    } catch (err) {
        alert('Failed to assign voice: ' + err.message);
    }
}
