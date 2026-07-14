const STUN_CONFIG = {
    iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
};

let localStream = null;
let voiceSocket = null;
let peers = {};      // { username: { pc: RTCPeerConnection, channel_name: string } }
let isMuted = false;
let inCall = false;

async function joinCall() {
    if (inCall) return;
    try {
        localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    } catch (err) {
        alert('Microphone permission denied. Please allow microphone access to join the call.');
        return;
    }

    voiceSocket = new WebSocket(`ws://${window.location.host}/ws/voice/${groupId}/`);

    voiceSocket.onmessage = async (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'peer_joined' && data.peer_id !== currentUser) {
            await createPeerConnection(data.peer_id, data.channel_name, true);
        }
        else if (data.type === 'peer_left') {
            removePeer(data.peer_id);
        }
        else if (data.type === 'offer') {
            const pc = await createPeerConnection(data.from_peer, data.from_channel, false);
            await pc.setRemoteDescription(new RTCSessionDescription({ type: 'offer', sdp: data.sdp }));
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);
            voiceSocket.send(JSON.stringify({
                type: 'answer',
                target: data.from_channel,
                sdp: answer.sdp,
            }));
        }
        else if (data.type === 'answer') {
            const peer = peers[data.from_peer];
            if (peer) await peer.pc.setRemoteDescription(
                new RTCSessionDescription({ type: 'answer', sdp: data.sdp })
            );
        }
        else if (data.type === 'ice_candidate') {
            const peer = peers[data.from_peer];
            if (peer && data.candidate) {
                await peer.pc.addIceCandidate(new RTCIceCandidate(data.candidate));
            }
        }
    };

    voiceSocket.onopen = () => {
        inCall = true;
        updateCallUI();
    };

    voiceSocket.onclose = () => leaveCall();
}

async function createPeerConnection(peerId, peerChannelName, isInitiator) {
    if (peers[peerId]) return peers[peerId].pc;
    
    const pc = new RTCPeerConnection(STUN_CONFIG);
    peers[peerId] = { pc, channel_name: peerChannelName };

    localStream.getTracks().forEach(track => pc.addTrack(track, localStream));

    pc.onicecandidate = (event) => {
        if (event.candidate && voiceSocket.readyState === WebSocket.OPEN) {
            voiceSocket.send(JSON.stringify({
                type: 'ice_candidate',
                target: peerChannelName,
                candidate: event.candidate,
            }));
        }
    };

    pc.ontrack = (event) => {
        let audio = document.getElementById(`audio-${peerId}`);
        if (!audio) {
            audio = document.createElement('audio');
            audio.id = `audio-${peerId}`;
            audio.autoplay = true;
            document.body.appendChild(audio);
        }
        audio.srcObject = event.streams[0];
        addPeerToUI(peerId);
    };

    if (isInitiator) {
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        voiceSocket.send(JSON.stringify({
            type: 'offer',
            target: peerChannelName,
            sdp: offer.sdp,
        }));
    }

    return pc;
}

function removePeer(peerId) {
    if (peers[peerId]) {
        peers[peerId].pc.close();
        delete peers[peerId];
    }
    const audio = document.getElementById(`audio-${peerId}`);
    if (audio) audio.remove();
    removePeerFromUI(peerId);
}

function leaveCall() {
    Object.keys(peers).forEach(removePeer);
    if (localStream) {
        localStream.getTracks().forEach(t => t.stop());
        localStream = null;
    }
    if (voiceSocket && voiceSocket.readyState === WebSocket.OPEN) {
        voiceSocket.close();
    }
    voiceSocket = null;
    inCall = false;
    peers = {};
    updateCallUI();
}

function toggleMute() {
    if (!localStream) return;
    isMuted = !isMuted;
    localStream.getAudioTracks().forEach(track => { track.enabled = !isMuted; });
    updateMuteButton();
}

function updateCallUI() {
    const joinBtn = document.getElementById('join-call-btn');
    const inCallPanel = document.getElementById('in-call-panel');
    if (joinBtn) joinBtn.style.display = inCall ? 'none' : 'flex';
    if (inCallPanel) inCallPanel.style.display = inCall ? 'flex' : 'none';
}

function updateMuteButton() {
    const btn = document.getElementById('mute-btn');
    if (!btn) return;
    btn.innerHTML = isMuted
        ? '<i data-lucide="mic-off" class="w-4 h-4 text-red-400"></i>'
        : '<i data-lucide="mic" class="w-4 h-4"></i>';
    if (window.lucide) lucide.createIcons();
}

function addPeerToUI(peerId) {
    const container = document.getElementById('call-peers');
    if (!container || document.getElementById(`peer-avatar-${peerId}`)) return;
    const initials = peerId.substring(0, 2).toUpperCase();
    container.insertAdjacentHTML('beforeend',
        `<div id="peer-avatar-${peerId}"
              class="w-8 h-8 rounded-full bg-[#D0BCFF]/20 border border-[#D0BCFF]/40
                     flex items-center justify-center text-xs font-bold text-[#D0BCFF]"
              title="${peerId}">${initials}</div>`
    );
}

function removePeerFromUI(peerId) {
    const el = document.getElementById(`peer-avatar-${peerId}`);
    if (el) el.remove();
}