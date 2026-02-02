document.addEventListener('DOMContentLoaded', () => {
    
    // Select both CTA buttons (Hero and Footer)
    const ctaButtons = document.querySelectorAll('#cta-upload-hero, #cta-upload-footer');

    ctaButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Visual feedback
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Preparing Cockpit...';
            
            // Simulate a brief delay for effect, then redirect
            setTimeout(() => {
                // Redirect to the next step (Step 2)
                // Since we are in a hackathon, we assume the next file will be upload.html
                window.location.href = 'upload.html'; 
            }, 800);
        });
    });

    // --- Upload Page Logic ---
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    const analysisStatus = document.getElementById('analysis-status');
    const progressBar = document.getElementById('progress-bar');
    const statusText = document.getElementById('status-text');
    const fileNameDisplay = document.getElementById('filename');

    // Only run if we are on the upload page
    if (dropZone) {
        // Handle Browse Button
        browseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.click();
        });

        // Handle Click on Zone
        dropZone.addEventListener('click', () => fileInput.click());

        // Drag & Drop Events
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.add('drag-over'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-over'), false);
        });

        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length) handleFiles(files[0]);
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) handleFiles(e.target.files[0]);
        });

        function handleFiles(file) {
            // UI Transition
            dropZone.style.display = 'none';
            analysisStatus.style.display = 'block';
            fileNameDisplay.textContent = file.name;
            statusText.textContent = "Uploading and analyzing with AI...";
            progressBar.style.width = '30%';

            // Create Form Data
            const formData = new FormData();
            formData.append('resume', file);

            // Send to Backend
            fetch('/api/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server Error: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }

                progressBar.style.width = '100%';
                statusText.textContent = "Analysis Complete! Redirecting...";
                
                // Save the AI data to LocalStorage so the Dashboard can use it
                localStorage.setItem('applyNinjaUser', JSON.stringify(data));
                
                // Check if user came from Payment Page (Pending Premium)
                if (localStorage.getItem('pendingPremium') === 'true') {
                    statusText.textContent = "Activating Pro Plan...";
                    fetch('/api/verify-payment', { method: 'POST' })
                        .then(() => {
                            localStorage.removeItem('pendingPremium');
                            // Update local data to reflect premium
                            data.is_premium = true;
                            localStorage.setItem('applyNinjaUser', JSON.stringify(data));
                            setTimeout(() => window.location.href = 'dashboard.html', 1000);
                        });
                } else {
                    setTimeout(() => window.location.href = 'dashboard.html', 1000);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                statusText.textContent = "Error: " + error.message;
                statusText.style.color = "#ef4444";
            });
        }
    }

    // --- Dashboard Logic ---
    const jobListBody = document.getElementById('job-list-body');
    if (jobListBody) {
        // 1. Load User Name from AI Data
        const storedData = localStorage.getItem('applyNinjaUser');
        
        // --- DEBUG: Check what is in storage ---
        console.log("🔍 Dashboard loaded. Checking LocalStorage for 'applyNinjaUser'...");
        console.log("📦 Raw Data:", storedData);
        // ---------------------------------------

        if (storedData) {
            const data = JSON.parse(storedData);
            const userNameEl = document.querySelector('.user-name');
            if (data && data.name && userNameEl) {
                userNameEl.textContent = data.name;
            }
        }

        // 2. Handle Google Search Button
        const searchBtn = document.getElementById('google-search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                const storedData = localStorage.getItem('applyNinjaUser');
                if (storedData) {
                    const data = JSON.parse(storedData);
                    let queryParts = [];

                    // Build query: "Role + Top 3 Skills + jobs"
                    if (data.job_role) {
                        queryParts.push(data.job_role);
                    }
                    if (data.skills && Array.isArray(data.skills)) {
                        queryParts.push(...data.skills.slice(0, 3));
                    }
                    queryParts.push("jobs");

                    const queryString = queryParts.join(" ");
                    const googleUrl = `https://www.google.com/search?q=${encodeURIComponent(queryString)}&ibp=htl;jobs`;
                    window.open(googleUrl, '_blank');
                } else {
                    alert("Please upload a resume first.");
                }
            });
        }

        // 3. Handle LinkedIn Pilot
        const linkedinBtn = document.getElementById('linkedin-btn');
        const modal = document.getElementById('linkedin-modal');
        const closeModal = document.getElementById('close-modal');
        const linkedinForm = document.getElementById('linkedin-form');
        const stopBtn = document.getElementById('stop-bot-btn');
        
        const paymentModal = document.getElementById('payment-modal');
        const verifyPaymentBtn = document.getElementById('verify-payment-btn');

        if (linkedinBtn && modal) {
            // Open Modal
            linkedinBtn.addEventListener('click', () => {
                modal.style.display = "block";
                if (stopBtn) stopBtn.style.display = "none"; // Reset state
            });

            // Close Modal
            closeModal.addEventListener('click', () => {
                modal.style.display = "none";
            });

            // Submit Credentials
            linkedinForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const email = document.getElementById('li-email').value;
                const password = document.getElementById('li-password').value;

                modal.style.display = "none"; // Close modal immediately
                
                // UI Feedback
                alert("🤖 LinkedIn Agent Deployed! Watch the server terminal.");
                if (stopBtn) stopBtn.style.display = "inline-flex"; // Show Stop Button

                fetch('/api/linkedin-apply', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                })
                .then(response => response.json())
                .then(data => {
                    if(data.error) {
                        if (data.error.includes("PAYMENT_REQUIRED")) {
                            paymentModal.style.display = "block";
                        } else {
                            alert("Agent Error: " + data.error);
                        }
                    }
                    else alert("✅ " + data.message);
                })
                .catch(err => alert("Network Error: " + err))
                .finally(() => {
                    if (stopBtn) stopBtn.style.display = "none"; // Hide Stop Button when done
                });
            });
        }

        // Handle Payment Verification
        if (verifyPaymentBtn) {
            verifyPaymentBtn.addEventListener('click', () => {
                verifyPaymentBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Verifying...';
                fetch('/api/verify-payment', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    alert("🎉 " + data.message);
                    paymentModal.style.display = "none";
                    verifyPaymentBtn.innerHTML = 'I Have Paid';
                    // Optionally restart the bot here or ask user to click again
                })
                .catch(err => alert("Verification Failed"));
            });
        }

        // 4. Handle Stop Bot
        if (stopBtn) {
            stopBtn.addEventListener('click', () => {
                fetch('/api/stop-bot', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    alert("🛑 " + data.message);
                    stopBtn.style.display = "none";
                })
                .catch(err => alert("Error stopping bot: " + err));
            });
        }

        // Mock Data for Hackathon Demo
        const jobs = [
            { company: "TechCorp AI", role: "Senior Frontend Engineer", match: "98%", status: "Interview", date: "2 hours ago" },
            { company: "Innovate Systems", role: "Full Stack Developer", match: "95%", status: "Applied", date: "5 hours ago" },
            { company: "DataFlow Inc", role: "React Specialist", match: "88%", status: "Applied", date: "1 day ago" },
            { company: "CloudScale", role: "UI/UX Engineer", match: "92%", status: "Applied", date: "1 day ago" },
            { company: "OldSchool Bank", role: "Web Developer", match: "75%", status: "Rejected", date: "2 days ago" }
        ];

        // Render Rows
        jobs.forEach(job => {
            const row = document.createElement('tr');
            
            // Determine status class
            let statusClass = 'applied';
            if (job.status === 'Interview') statusClass = 'interview';
            if (job.status === 'Rejected') statusClass = 'rejected';

            row.innerHTML = `
                <td>
                    <div style="display:flex; align-items:center;">
                        <div class="company-logo-placeholder"><i class="fa-solid fa-building"></i></div>
                        ${job.company}
                    </div>
                </td>
                <td>${job.role}</td>
                <td><span class="match-score">${job.match}</span></td>
                <td><span class="status-badge ${statusClass}"><i class="fa-solid fa-circle" style="font-size: 6px;"></i> ${job.status}</span></td>
                <td style="color: var(--text-light); font-size: 0.9rem;">${job.date}</td>
            `;
            jobListBody.appendChild(row);
        });
    }

    // --- Settings Page Logic ---
    const settingsForm = document.getElementById('settings-form');
    if (settingsForm) {
        const storedData = localStorage.getItem('applyNinjaUser');
        if (storedData) {
            const data = JSON.parse(storedData);
            
            // Populate fields
            if (data.name) document.getElementById('name').value = data.name;
            if (data.job_role) document.getElementById('job_role').value = data.job_role;
            
            // Handle skills array -> string
            if (data.skills && Array.isArray(data.skills)) {
                document.getElementById('skills').value = data.skills.join(', ');
            }

            // Show Raw JSON
            document.getElementById('raw-json').textContent = JSON.stringify(data, null, 4);
        }

        settingsForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Get current data to preserve other fields (like email, phone, etc.)
            let currentData = JSON.parse(localStorage.getItem('applyNinjaUser')) || {};
            
            // Update fields
            currentData.name = document.getElementById('name').value;
            currentData.job_role = document.getElementById('job_role').value;
            
            // Handle skills string -> array
            const skillsString = document.getElementById('skills').value;
            currentData.skills = skillsString.split(',').map(s => s.trim()).filter(s => s.length > 0);

            // Save back
            localStorage.setItem('applyNinjaUser', JSON.stringify(currentData));
            
            alert('Settings Saved!');
            window.location.href = 'dashboard.html';
        });
    }

    // --- History Page Logic ---
    const historyTableBody = document.getElementById('history-table-body');
    if (historyTableBody) {
        const loadHistory = () => {
            fetch('/api/history')
                .then(response => response.json())
                .then(data => {
                    historyTableBody.innerHTML = ''; // Clear loading state
                    
                    if (data.length === 0) {
                        historyTableBody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 2rem; color: #64748b;">No applications logged yet.</td></tr>';
                        return;
                    }

                    data.forEach(item => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td><i class="fa-solid fa-building" style="color:var(--text-light); margin-right:8px;"></i> ${item.company}</td>
                            <td>${item.role}</td>
                            <td><span class="status-badge applied"><i class="fa-solid fa-check"></i> ${item.status}</span></td>
                            <td style="color: var(--text-light); font-size: 0.9rem;">${item.date}</td>
                        `;
                        historyTableBody.appendChild(row);
                    });
                });
        };

        // Initial Load
        loadHistory();

        // Auto-refresh every 3 seconds
        setInterval(loadHistory, 3000);

        // Handle Clear History
        const clearBtn = document.getElementById('clear-history-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                if (confirm("Are you sure you want to clear the application history?")) {
                    fetch('/api/history', { method: 'DELETE' })
                        .then(response => response.json())
                        .then(data => {
                            if (data.error) alert("Error: " + data.error);
                            else loadHistory(); // Refresh immediately
                        });
                }
            });
        }
    }

    // --- Payment Page Logic ---
    const paymentForm = document.getElementById('payment-proof-form');
    if (paymentForm) {
        paymentForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const fileInput = document.getElementById('proof-file');
            if (fileInput.files.length === 0) {
                alert("Please upload a screenshot of your payment.");
                return;
            }
            // Simulate upload/verification
            const btn = paymentForm.querySelector('button');
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Verifying...';
            
            setTimeout(() => {
                localStorage.setItem('pendingPremium', 'true');
                alert("Payment proof submitted successfully! Please upload your resume to activate Pro features.");
                window.location.href = 'upload.html';
            }, 1500);
        });
    }

    // --- Slow Smooth Scroll for Anchor Links ---
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#' || !document.querySelector(targetId)) return;
            
            e.preventDefault();
            const targetElement = document.querySelector(targetId);
            const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset;
            const startPosition = window.pageYOffset;
            const distance = targetPosition - startPosition;
            const duration = 1500; // 1.5 seconds for slower animation
            let start = null;

            function step(timestamp) {
                if (!start) start = timestamp;
                const progress = timestamp - start;
                // Ease-in-out cubic
                const ease = (t) => t < .5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
                
                window.scrollTo(0, startPosition + (distance * ease(Math.min(progress / duration, 1))));
                if (progress < duration) window.requestAnimationFrame(step);
            }
            window.requestAnimationFrame(step);
        });
    });

    // --- FAQ Accordion Logic ---
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        question.addEventListener('click', () => {
            // Close others
            faqItems.forEach(otherItem => {
                if (otherItem !== item) otherItem.classList.remove('active');
            });
            // Toggle current
            item.classList.toggle('active');
        });
    });

    // --- Contact Form Logic ---
    const contactForm = document.getElementById('contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const btn = contactForm.querySelector('button');
            const originalText = btn.innerText;
            
            btn.innerText = 'Sending...';
            btn.disabled = true;

            const name = document.getElementById('contact-name').value;
            const email = document.getElementById('contact-email').value;
            const message = document.getElementById('contact-message').value;

            fetch('/api/contact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, message })
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                contactForm.reset();
            })
            .catch(err => alert("Error sending message."))
            .finally(() => {
                btn.innerText = originalText;
                btn.disabled = false;
            });
        });
    }

    // --- Back to Top Button ---
    const backToTopBtn = document.getElementById("back-to-top");

    if (backToTopBtn) {
        window.addEventListener('scroll', () => {
            if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
                backToTopBtn.style.display = "block";
            } else {
                backToTopBtn.style.display = "none";
            }
        });

        backToTopBtn.addEventListener("click", function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
});
