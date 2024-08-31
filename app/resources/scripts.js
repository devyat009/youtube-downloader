// scripts here
document.addEventListener('DOMContentLoaded', function() {
    // Flag to track download status.
    let downloadInProgress = false;
    // Track the process_url and download_thumbnail time to process.
    let get_video_formats = null; // received in showMessage and used to process_url.
    let thumbnail_download_check = null; // received in showMessage and used to handleThumbnail.
    let elapsedTime = 0;
    const intervalTime = 1000; // 
    // Validation to initiate download. Ensure the user selects an resolution and path.
    let selected_resolution = null;
    let selected_path = null;
    ;
    
    // Initialize the QWebChannel and connect to the backend object.
    new QWebChannel(qt.webChannelTransport, function(channel) {
        window.backend = channel.objects.backend;

        // Download/Cancel Button
        document.getElementById('downloadBtn').addEventListener('click', function() {
            const button = document.getElementById('downloadBtn');

            if (downloadInProgress) {
                // Cancel the download if in progress
                if (window.backend) {
                    window.backend.cancel_download().then(function() {
                        showError("Download canceled.");
                        downloadInProgress = false; // Update the flag
                        button.innerHTML = `
                            <svg class="download-icon" viewBox="0 0 384 512" height="1em" xmlns="http://www.w3.org/2000/svg">
                                <path d="M169.4 470.6c12.5 12.5 32.8 12.5 45.3 0l160-160c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L224 370.8 224 64c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 306.7L54.6 265.4c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3l160 160z"></path>
                            </svg>
                            Download
                        `;
                        button.className = 'download-btn';
                        document.getElementById("progress-label").innerText = ``;
                        const progressBar = document.querySelector('.progress-bar');
                        progressBar.style.width = `0%`;
                    }).catch(function(error) {
                        showError("Error while canceling the download: " + error)
                        console.log("Error while canceling the download: " + error);
                    });
                }
            } else {
                // Start the download if not in progress
                if (window.backend) {
                    if (selected_resolution !== null && selected_path !== null) {
                        window.backend.download_vid().then(function(response) {
                            console.log(response);
                            button.innerHTML = `
                            <svg class="cancel-icon" xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" width="16" height="16" viewBox="0 0 24 24">
                                <path d="M 4.9902344 3.9902344 A 1.0001 1.0001 0 0 0 4.2929688 5.7070312 L 10.585938 12 L 4.2929688 18.292969 A 1.0001 1.0001 0 1 0 5.7070312 19.707031 L 12 13.414062 L 18.292969 19.707031 A 1.0001 1.0001 0 1 0 19.707031 18.292969 L 13.414062 12 L 19.707031 5.7070312 A 1.0001 1.0001 0 0 0 18.980469 3.9902344 A 1.0001 1.0001 0 0 0 18.292969 4.2929688 L 12 10.585938 L 5.7070312 4.2929688 A 1.0001 1.0001 0 0 0 4.9902344 3.9902344 z"></path>
                            </svg>
                            Cancel
                            `;
                            button.className = "cancel-btn"
                            downloadInProgress = true; // Update the flag
                            document.getElementById("progress-label").innerText = `Waiting download start...`;
                            const progressBar = document.querySelector('.progress-bar');
                            progressBar.style.width = `0%`;
                        }).catch(function(error) {
                            showError("Error while starting the download: " + error)
                            console.log("Error while starting the download: " + error);
                        });
                    } else if (selected_resolution === null && selected_path !== null){
                        showError('Select any resolution available to continue.');
                    } else if (selected_resolution !== null && selected_path === null){
                        showError('Choose the path to continue.');
                    } else {
                        showError('Please insert a path and select a resolution.');
                    }
                } else {
                    showError("Something went wrong trying to download.")
                    console.log("Something went wrong trying to download");
                }
            }
        });

         // Update Download Progress
        window.backend.download_progress_signal.connect(function(percent, total_size, time, d_speed) {
            updateProgress(percent, total_size, time, d_speed);
        });

        // Receive Errors from backend.
        if (window.backend && window.backend.errorSignal) {
            window.backend.errorSignal.connect(function(message) {
                showError(message);
            });
        }
        // Receive Messages from backend.
        if (window.backend && window.backend.messageSignal) {
            window.backend.messageSignal.connect(function(message){
                showMessage(message)
            });
        }
    });

    // Get URL by click or enter key press.
    document.getElementById('sendFind').addEventListener('click', function() {
        get_url();
    });
    document.getElementById('url1').addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            get_url();
        }
    });
    // Execute the url process.
    function get_url() {
        const message = document.getElementById('url1').value;
        if (window.backend) {
            window.backend.process_url(message).then(function(response) {
                const screenOverlay = document.createElement('div');
                screenOverlay.id = 'loadingOverlay';
                screenOverlay.className = 'screenOverlay';

                const loadingBar = document.createElement('div');
                loadingBar.className = 'loadingBar';
                // Add to the screen
                document.body.appendChild(screenOverlay);
                screenOverlay.appendChild(loadingBar);
                function killOverlay(){
                    document.body.removeChild(screenOverlay);
                };
                function checkCondition(){
                    if (get_video_formats === 'success') {
                        killOverlay();
                        handleThumbnail();
                        handleResolutionOptions();
                        handleFiletypeOptions()
                        clearInterval(intervalId);
                        get_video_formats = null;
                    } else {
                        elapsedTime += intervalTime / 1000;
                        if (elapsedTime >= 60) {
                            showError('Stopping the check after 60 seconds. Its taking too much time to process the URL... try again');
                            clearInterval(intervalId); // Stop checking after 60s
                            killOverlay();
                        }
                    }
                }
                let intervalId = setInterval(checkCondition, intervalTime);
            });
        } else {
            console.log('Backend is not ready');
            showError("Backend is not ready...")
        }
    };

    // Thumbnail Changer //
    function handleThumbnail () {
        window.backend.get_thumbnail().then(function(imagePath) {
            if (imagePath === "Image Not Found") {
                document.querySelector('.image-icon').style.fill = '#FFFFF';
            } else {
                const clean = document.querySelector('.thumbnail-box');
                clean.innerHTML= '';
                // If found will change the thumbnail-box
                document.querySelector('.thumbnail-box').style.backgroundImage = `url(${imagePath})`;
                
                // Create the thumbnail download button
                const thumbnail_download = document.createElement('button');
                thumbnail_download.id = 'thumbnail-download';
                thumbnail_download.className = 'thumbnail-downloadButton';
                thumbnail_download.innerHTML = `
                    <svg class="download-icon" viewBox="0 0 384 512" height="1em" xmlns="http://www.w3.org/2000/svg">
                        <path d="M169.4 470.6c12.5 12.5 32.8 12.5 45.3 0l160-160c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L224 370.8 224 64c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 306.7L54.6 265.4c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3l160 160z"></path>
                    </svg>
                    <text class="thumbnail_downloadText">Download</text>`;
                document.querySelector('.thumbnail-box').appendChild(thumbnail_download);
                // Download Thumbnail
                document.getElementById('thumbnail-download').addEventListener('click', function(nothing) { 
                    window.backend.download_thumbnail();
                    console.log(nothing);

                    const overlay = document.createElement('div');
                    overlay.className = 'screenOverlay';

                    const loadingBar = document.createElement('div');
                    loadingBar.className = 'loadingBar';

                    document.body.appendChild(overlay);
                    overlay.appendChild(loadingBar);
                    function killOverlay(){
                        document.body.removeChild(overlay);
                    };
                    function checkCondition(){
                        console.log('checking coditions');
                        if (thumbnail_download_check === 'finished' && selected_path !== null) {
                            console.log('condition thumbbnail met');
                            killOverlay();
                            clearInterval(intervalId);
                            thumbnail_download_check = null;
                            showMessage('thumbnail finished')
                        } else if (selected_path === null) { 
                            killOverlay();
                            showError('Please select the path before downloading');
                            clearInterval(intervalId);
                        } else {
                            elapsedTime += intervalTime / 1000;
                            if (elapsedTime >= 60) {
                                showError('Stopping the check after 60 seconds. Its taking too much time to process the URL... try again');
                                clearInterval(intervalId); // Stop checking after 60s
                                killOverlay();
                            }
                        }
                    }
                    let intervalId = setInterval(checkCondition, intervalTime);
                    
                });
            }
        });
    };

    // Get Resolution options //
    function handleResolutionOptions () {
        window.backend.get_resolution_options().then(function(options) {
            // Check later if is needed this line: 
            const clean = document.querySelector('.options-resolution');
            clean.innerHTML= '';
            options.forEach(function(option) {
                const item = document.createElement('div');
                item.textContent = option;
                item.className = "option-resolution";
                item.addEventListener('click', function(){
                    document.querySelector('.select-resolution .text').textContent = option;
                    document.querySelector('.select-resolution .text').style.fontSize = "10px";
                    closeDropdownResolution();

                    // Send backend the selected option
                    window.backend.set_selected_resolution(option);
                    selected_resolution = option;
                });
                document.querySelector('.options-resolution').appendChild(item);
            })
        });
    };

    // Get Filetype options //
    function handleFiletypeOptions () {
        window.backend.get_file_options().then(function(options) {
            const clean = document.querySelector('.options-filetype');
            clean.innerHTML= '';
            options.forEach(function(option) {
                const item = document.createElement('div');
                item.textContent = option
                item.className = "option-filetype";
                item.addEventListener('click', function(){
                    document.querySelector('.select-filetype .text').textContent = option;
                    document.querySelector('.select-filetype .text').style.fontSize = '13px';
                    closeDropdownFiletype();

                    // Send to the backend the selected option: (WIP)
                    //window.backend.set_selected_filetype(option);
                });
                document.querySelector('.options-filetype').appendChild(item);
            });
        });
    };
    
    // Update download progress label
    function updateProgress(percent, total_size, time, d_speed) {
            // Flag to track download finsiheed.
            let totalDownloads = 1; // Total downloads check
            let completedDownloads = 0;
            let downloadFinished = false
            document.getElementById("progress-label").innerText = `${percent}% of ${total_size} - ETA: ${time} - Speed: ${d_speed}`;
            document.getElementById("progress-label").style.marginLeft = '120px'; // Will asways ensure it will stay in the same place
            document.getElementById("progress-label").style.fontSize = '11px';
            const progressBar = document.querySelector('.progress-bar');
            const downloadButton = document.getElementById('downloadBtn');
            progressBar.style.width = `${percent}%` ;
            // Check if the download has finished and the message hasn't been set yet, because it downloads the video first and in sequence the audio.
            if (percent === '100') {
                if (!downloadFinished) {
                    completedDownloads++;
                    // Update the progress-label
                    if (completedDownloads === totalDownloads && !downloadFinished) {
                        document.getElementById("progress-label").innerText = "Download finished!";
                        document.getElementById("progress-label").style.marginLeft = '150px'; // Will asways ensure it will stay in the same place
                        downloadFinished = true; // Ensure "Download finished!" will be seen one time.
                        downloadInProgress = false; // Reset the download progress flag
                        downloadButton.innerHTML = `
                            <svg class="download-icon" viewBox="0 0 384 512" height="1em" xmlns="http://www.w3.org/2000/svg">
                                <path d="M169.4 470.6c12.5 12.5 32.8 12.5 45.3 0l160-160c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L224 370.8 224 64c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 306.7L54.6 265.4c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3l160 160z"></path>
                            </svg>
                            Download
                        `;
                        downloadButton.className = 'download-btn';
                        progressBar.style.width = `0%`
                    }
                }
            }
        };

    // Get the path by Python Backend
    document.getElementById('sendPath').addEventListener('click', function() {
        if (window.backend) {
            window.backend.select_folder().then(function(response) {
                document.getElementById('path1').value = response;
                selected_path = response;
            });
        } else {
            console.log('Backend is not ready');
            showError("Backend is not ready.")
        }
    });

    // Close dropdowns.
    function closeAllDropdowns() {
        const allDropdowns = document.querySelectorAll('.options-filetype, .options-resolution');
        const allButtons = document.querySelectorAll('.select-filetype, .select-resolution');
        allDropdowns.forEach(dropdown => dropdown.style.display = 'none');
    }

    
    // Resolution DROPDOWN Mouse on Enter and Leave //
    const optionsResolution = document.querySelector('.options-resolution');
    const selectResolution = document.querySelector('.select-resolution');
    const selectFiletype = document.querySelector('.select-filetype');
    const optionsFiletype = document.querySelector('.options-filetype');
    // Open functions
    function openDropdownResolution() {
        closeAllDropdowns(); // Ensure close any other dropdown.
        optionsResolution.style.display = 'block';
        optionsResolution.style.top = '43px';
    }
    function openDropdownFiletype() {
        closeAllDropdowns();
        optionsFiletype.style.display = 'block';
        optionsFiletype.style.top = '43px';
    }
    // Close Functions  
    function closeDropdownResolution() {
        //dropdownResolution.style.opacity = '0'; // If use this, anywhere that passs below the button will show up along opacity 1 above
        optionsResolution.style.display = 'none';
        //dropdownResolutionBTN.style.borderRadius = '10px'; // Restaura o border-radius original
    }
    function closeDropdownFiletype() {
        optionsFiletype.style.display = 'none';
    }
    selectResolution.addEventListener('mouseenter', openDropdownResolution);
    selectFiletype.addEventListener('mouseenter', openDropdownFiletype);
    //dropdownResolutionBTN.addEventListener('mouseleave', closeDropdown);
    optionsResolution.addEventListener('mouseleave', closeDropdownResolution);
    optionsFiletype.addEventListener('mouseleave', closeDropdownFiletype);
    
    // Show errors on screen.
    function showError(message) {
        // Creates the alert container.
        const alertBox = document.createElement('div');
        alertBox.id = 'customAlert';
        alertBox.className = 'custom-alert';

        // Create the alert message.
        const alertMessage = document.createElement('span');
        alertMessage.id = 'alertMessage';
        alertMessage.textContent = message;

        // Create the close button.
        const closeButton = document.createElement('button');
        closeButton.textContent = 'Close';
        closeButton.onclick = function() {
            document.body.removeChild(alertBox); // Close the alert after clicking on close.
        };

        // Add the message to the alert container.
        alertBox.appendChild(alertMessage);
        alertBox.appendChild(closeButton);

        // Add the alert container to the body.
        document.body.appendChild(alertBox);

        // Vanish alert after 15s
        setTimeout(function() {
            if (document.body.contains(alertBox)) {
                document.body.removeChild(alertBox);
            }
        }, 15000); // 15000ms = 15s.
    };

    // Custom Messages
    function showMessage(message) {
        if (message === 'Vid and Aud merged') {
            const popUpContainer = document.createElement('div');
            popUpContainer.id = 'customMessageMerged';
            popUpContainer.className = 'popUpContainer';
            // Screen Overlay
            const overlay = document.createElement('div');
            overlay.id = 'screenOverly';
            overlay.className = 'screenOverlay';
            
            // Simple Message
            const popUp = document.createElement('text');
            popUp.textContent = 'Video and Audio merged successfully';
            popUp.id = 'vid_aud_merged';
            popUp.className = 'popUpTextContent';

            // See Folder
            const openFolder = document.createElement('button');
            openFolder.className = 'openFolderButton';
            openFolder.innerHTML = `
                        <svg class="openPath-icon" class="custom-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="-3 -3 30 30" fill="none">
                            <g stroke-width="2" stroke-linecap="round" fill-rule="evenodd" clip-rule="evenodd">
                                <path d="M3 7H20C20.5523 7 21 7.44772 21 8V19C21 19.5523 20.5523 20 20 20H4C3.44772 20 3 19.5523 3 19V8C3 7.44772 3.44772 7 4 7Z"></path>
                                <path d="M3 4.5C3 4.22386 3.22386 4 3.5 4H9.79289C9.9255 4 10.0527 4.05268 10.1464 4.14645L13 7H3V4.5Z"></path>
                            </g>
                        </svg>
                        <textContent class="openTextContent">Open Folder</textContent>
                        `;
            openFolder.onclick = function () {
                console.log('The openFolder button has been clicked')
                window.backend.openFolder().then(function(success){
                    if (success) {
                        document.body.removeChild(overlay);
                    } else {
                        showError("Failed to open folder.");
                    }
                });
            };

            // Stay
            const stay = document.createElement('button');
            stay.className = 'stayButton';
            stay.innerHTML = `
                        <svg class="cancel-icon" xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" width="16" height="16" viewBox="0 0 24 24">
                            <path d="M 4.9902344 3.9902344 A 1.0001 1.0001 0 0 0 4.2929688 5.7070312 L 10.585938 12 L 4.2929688 18.292969 A 1.0001 1.0001 0 1 0 5.7070312 19.707031 L 12 13.414062 L 18.292969 19.707031 A 1.0001 1.0001 0 1 0 19.707031 18.292969 L 13.414062 12 L 19.707031 5.7070312 A 1.0001 1.0001 0 0 0 18.980469 3.9902344 A 1.0001 1.0001 0 0 0 18.292969 4.2929688 L 12 10.585938 L 5.7070312 4.2929688 A 1.0001 1.0001 0 0 0 4.9902344 3.9902344 z"></path>
                        </svg>
                        <textContent class="stayTextContent">Close</textContent>
                        `;
            stay.onclick = function() {
                document.body.removeChild(overlay); // Deletes the Overlay
            };
            
            // Append the child items
            popUpContainer.appendChild(popUp);
            popUpContainer.appendChild(openFolder);
            popUpContainer.appendChild(stay);

            // Add the popUp to the document body.
            overlay.appendChild(popUpContainer);
            document.body.appendChild(overlay);

            
        }
        // Used to receive the communication between backend get_video_formats thread
        else if (message === 'get_video_formats finished') {
            get_video_formats = 'success';
        }
        else if (message === 'downloading') {
            thumbnail_download = 'started';
        }
        else if (message === 'thumbnail downloaded') {
            thumbnail_download_check = 'finished';
        }
        else if (message === 'thumbnail finished') {
            const thumbnailPopUpContainer = document.createElement('div');
            thumbnailPopUpContainer.className = 'thumbnailPopUpContainer';

            // Screen Overlay
            const overlay = document.createElement('div');
            overlay.id = 'screenOverly';
            overlay.className = 'screenOverlay';

            // Simple Message
            const popUp = document.createElement('text');
            popUp.textContent = 'Thumbnail was downloaded successfully';
            popUp.className = 'popUpTextContent';

            // See Folder
            const openFolder = document.createElement('button');
            openFolder.className = 'openFolderButton';
            openFolder.innerHTML = `
                        <svg class="openPath-icon" class="custom-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="-3 -3 30 30" fill="none">
                            <g stroke-width="2" stroke-linecap="round" fill-rule="evenodd" clip-rule="evenodd">
                                <path d="M3 7H20C20.5523 7 21 7.44772 21 8V19C21 19.5523 20.5523 20 20 20H4C3.44772 20 3 19.5523 3 19V8C3 7.44772 3.44772 7 4 7Z"></path>
                                <path d="M3 4.5C3 4.22386 3.22386 4 3.5 4H9.79289C9.9255 4 10.0527 4.05268 10.1464 4.14645L13 7H3V4.5Z"></path>
                            </g>
                        </svg>
                        <textContent class="openTextContent">Open Folder</textContent>
                        `;
            openFolder.onclick = function () {
                window.backend.openFolder().then(function(success){
                    if (success) {
                        document.body.removeChild(thumbnailPopUpContainer);
                        document.body.removeChild(overlay);
                    } else {
                        showError("Failed to open folder.");
                    }
                });
            };
            // Add the button to the container.
            thumbnailPopUpContainer.appendChild(popUp);
            thumbnailPopUpContainer.appendChild(openFolder);
            // Add to the body.
            document.body.appendChild(overlay);
            document.body.appendChild(thumbnailPopUpContainer);

        }
    };

    // Prevent right mouse button click. (LATER ENABLE BEFORE BUILDING, IF COMMENTED RELOAD BUTTON WILL BE AVAILABLE)
    document.addEventListener('contextmenu', function(event) {
        event.preventDefault();
    });
});