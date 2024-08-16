// scripts here
document.addEventListener('DOMContentLoaded', function() {
    // Flag to track download status.
    let downloadInProgress = false;
    ;
    
    // Initialize the QWebChannel and connect to the backend object.
    new QWebChannel(qt.webChannelTransport, function(channel) {
        window.backend = channel.objects.backend;

        // Get the file type information every time it is click on the 'File Type' Dropdown button
        document.querySelector('.dropdown-btn').addEventListener('click', function() {
            // Limpa as opções existentes no dropdown
            const dropdown = document.querySelector('.dropdown-content-file');
            dropdown.innerHTML = '';
            // Get the file type options from the backend and populate the dropdown file type
            window.backend.get_file_options().then(function(options) {
                const dropdown = document.querySelector('.dropdown-content-file');
                const dropbtn = document.querySelector('.dropdown-btn');
                options.forEach(function(option) {
                    const item = document.createElement('div');
                    item.textContent = option;
                    item.addEventListener('click', function() {
                        document.querySelector('.dropdown-btn').textContent = option;
                        dropdown.style.display = 'none'; // Hide dropdown after selection
                        dropbtn.style.borderRadius = '10px';
                        dropdown.style.borderRadius = '0 0 10px 10px';
                    });
                    dropdown.appendChild(item);
                });
            });
        });
        // Resolution options for the dropdown button
        document.querySelector('.dropdown-btn-resolution').addEventListener('click', function() {
            // Clean the options on the dropdown
            const dropdown = document.querySelector('.dropdown-resolution-content');
            dropdown.innerHTML = '';
            // Get the resolution options from backend and populate the dropdown resolution
            window.backend.get_resolution_options().then(function(options) {
                const dropdownResolution = document.querySelector('.dropdown-resolution-content');
                const dropdownResolutionBTN = document.querySelector('.dropdown-btn-resolution');
                options.forEach(function(option) {
                    const item = document.createElement('div');
                    item.textContent = option;
                    item.addEventListener('click', function() {
                        document.querySelector('.dropdown-btn-resolution').textContent = option;
                        dropdownResolution.style.display = 'none'; // Hide dropdown after selection
                        dropdownResolutionBTN.style.borderRadius = '10px';
                        dropdownResolution.style.borderRadius = '0 0 10px 10px';

                        // Send back the selected option
                        window.backend.set_selected_resolution(option)
                    });
                    dropdownResolution.appendChild(item);
                })
            });
        });

        // Download/Cancel Button
        document.getElementById('downloadBtn').addEventListener('click', function() {
            const button = document.getElementById('downloadBtn');

            if (downloadInProgress) {
                // Cancel the download if in progress
                if (window.backend) {
                    window.backend.cancel_download().then(function() {
                        showError("Download canceled.");
                        button.textContent = 'Download'; // Change button text back to "Download"
                        downloadInProgress = false; // Update the flag
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
                    window.backend.download_vid().then(function(response) {
                        console.log("Download Started: " + response);
                        button.textContent = 'Cancel'; // Change button text to "Cancel"
                        downloadInProgress = true; // Update the flag
                        document.getElementById("progress-label").innerText = `Waiting download start...`;
                        const progressBar = document.querySelector('.progress-bar');
                        progressBar.style.width = `0%`;
                    }).catch(function(error) {
                        showError("Error while starting the download: " + error)
                        console.log("Error while starting the download: " + error);
                    });
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

        // Receive Errors or messages from backend.
        if (window.backend && window.backend.errorSignal) {
            window.backend.errorSignal.connect(function(message) {
                showError(message);
            });
        }
    });

    // Get URL
    document.getElementById('sendFind').addEventListener('click', function() {
        const message = document.getElementById('url1').value;
        if (window.backend) {
            window.backend.process_url(message).then(function(response) {
                document.getElementById('findResponse').innerText = response;

                // Thumbnail Changer
                window.backend.get_thumbnail().then(function(imagePath) {
                    const thumbnail = document.querySelector('.thumbnail-box');
                    thumbnail.style.backgroundImage = `url(${imagePath})`;
                });

            });
        } else {
            console.log('Backend is not ready');
            showError("Backend is not ready...")
        }
        
    });
    
    // Update download progress label
    function updateProgress(percent, total_size, time, d_speed) {
            // Flag to track download finsiheed.
            let totalDownloads = 1; // Total downloads check
            let completedDownloads = 0;
            let downloadFinished = false
            document.getElementById("progress-label").innerText = `${percent}% of ${total_size} - ETA: ${time} - Speed: ${d_speed}`;
            const progressBar = document.querySelector('.progress-bar');
            progressBar.style.width = `${percent}%` ;
            // Check if the download has finished and the message hasn't been set yet, because it downloads the video first and in sequence the audio.
            if (percent === '100') {
                if (!downloadFinished) {
                    completedDownloads++;
                    //console.log(`Download completed. Total completed downloads: ${completedDownloads}`);

                    // Update the progress-label
                    if (completedDownloads === totalDownloads && !downloadFinished) {
                        document.getElementById("progress-label").innerText = "Download finished!";
                        downloadFinished = true; // Ensure "Download finished!" will be seen one time.
                        downloadInProgress = false; // Reset the download progress flag
                        document.getElementById('downloadBtn').textContent = 'Download';
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
                //document.getElementById('pathResponse').innerText = "Folder selected: " + response;
            });
        } else {
            console.log('Backend is not ready');
            showError("Backend is not ready.")
        }
    });

    // Close dropdowns.
    function closeAllDropdowns() {
        const allDropdowns = document.querySelectorAll('.dropdown-content-file, .dropdown-resolution-content');
        const allButtons = document.querySelectorAll('.dropdown-btn, .dropdown-btn-resolution');
        allDropdowns.forEach(dropdown => dropdown.style.display = 'none');
        allButtons.forEach(button => button.style.borderRadius = '10px'); // Restaurar o border radius de todos os botões
    }

    document.querySelector('.dropdown-btn').addEventListener('click', function() {
        const dropdownContent = document.querySelector('.dropdown-content-file');
        const dropbtn = document.querySelector('.dropdown-btn');
        //dropdownContent.style.display = dropdownContent.style.  display === 'block' ? 'none' : 'block';
        //dropbtn.style.borderRadius = '10px 10px 0 0'; // No border on the bottom left and right after click on button.
        //dropdownContent.style.borderRadius = '0 0 10px 10px'; // No border on the top corner to match the code line above.
        if (dropdownContent.style.display === 'block') {
            dropdownContent.style.display = 'none';
            dropbtn.style.borderRadius = '10px'; // Restore the button border radius.
        } else {
            closeAllDropdowns();
            dropdownContent.style.display = 'block';
            dropbtn.style.borderRadius = '10px 10px 0 0'; // No border on the bottom corners when dropdown is open.
            dropdownContent.style.borderRadius= '0 0 10px 10px'; // No border on the top cornes to match the line above.
        }

    });

    // Dropdown Resolution button style changer and hider
    document.querySelector('.dropdown-btn-resolution').addEventListener('click', function(){
        const dropdownResolution = document.querySelector('.dropdown-resolution-content');
        const dropdownResolutionBTN = document.querySelector('.dropdown-btn-resolution');
        if (dropdownResolution.style.display === 'block') {
            dropdownResolution.style.display = 'none';
            dropdownResolutionBTN.style.borderRadius = '10px'; // Restore the border radius
        } else {
            closeAllDropdowns();
            dropdownResolution.style.display = 'block';
            dropdownResolutionBTN.style.borderRadius = '10px 10px 0 0 '; // No border on the bottom corners when dropdown is open.
            dropdownResolution.style.borderRadius= '0 0 10px 10px'; // No border on the top cornes to match the line above.
        }
    });
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.dropdown-file-type')){
            //document.querySelector('.dropdown-content-file').style.display = 'none';
            const dropdownContent = document.querySelector('.dropdown-content-file');
            const dropbtn = document.querySelector('.dropdown-btn');
            dropdownContent.style.display = 'none';
            dropbtn.style.borderRadius = '10px'; // Restore the button border radius when closing.
        }
    });

    document.addEventListener('click', function(event) {
        if (!event.target.closest('.dropdown-file-type')){
            //document.querySelector('.dropdown-content-file').style.display = 'none';
            const dropdownResolution = document.querySelector('.dropdown-resolution-content');
            const dropdownResolutionBTN = document.querySelector('.dropdown-btn-resolution');
            dropdownResolution.style.display = 'none';
            dropdownResolutionBTN.style.borderRadius = '10px'; // Restore the button border radius when closing.
        }
    });
    
    // Show errors on screen for the user.
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

    // Prevent right mouse button click. (LATER ENABLE BEFORE BUILDING)
    document.addEventListener('contextmenu', function(event) {
        event.preventDefault();
    });

    
});