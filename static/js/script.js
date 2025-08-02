let lastSpoken = null;

function updateVideoFeed() {
    const img = document.getElementById('videoFeed');
    img.onerror = () => {
        document.getElementById('message').innerHTML = '<div class="alert alert-danger">Error loading video feed</div>';
    };
    
    fetch('/video_feed', { method: 'GET' })
        .then(response => {
            const reader = response.body.getReader();
            let headers = '';
            
            function read() {
                reader.read().then(({ done, value }) => {
                    if (done) return;
                    
                    const text = new TextDecoder().decode(value);
                    if (text.includes('--frame')) {
                        headers = text.split('\r\n\r\n')[0];
                        const nameMatch = headers.match(/X-Name: (.*?)\r\n/);
                        const dateTimeMatch = headers.match(/X-DateTime: (.*?)\r\n/);
                        const name = nameMatch ? nameMatch[1] : 'None';
                        const dateTime = dateTimeMatch ? dateTimeMatch[1] : '';
                        
                        if (name === 'CameraError') {
                            document.getElementById('message').innerHTML = '<div class="alert alert-danger">Your device does not have a camera</div>';
                        } else if (name !== 'None' && name !== 'Unknown' && name !== lastSpoken) {
                            lastSpoken = name;
                            const message = `Face matched for ${name}`;
                            document.getElementById('message').innerHTML = `<div class="alert alert-success">${message} at ${dateTime}</div>`;
                            const utterance = new SpeechSynthesisUtterance(message);
                            utterance.rate = 1.2;
                            utterance.volume = 1.0;
                            window.speechSynthesis.speak(utterance);
                        }
                    }
                    
                    img.src = '/video_feed?' + new Date().getTime();
                    read();
                });
            }
            read();
        });
}

document.addEventListener('DOMContentLoaded', updateVideoFeed);