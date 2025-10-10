// ============================================
// DRIVER FRONTEND - WebSocket Notification System
// ============================================

// This JavaScript replaces the polling system with push notifications
// Place this in your driver.html <script> section

const API_URL = 'http://localhost:8000/api';
const WS_URL = 'ws://localhost:8000';

let currentDriver = JSON.parse(localStorage.getItem('currentUser'));
if (!currentDriver) {
    window.location.href = 'login.html';
}

const DRIVER_ID = currentDriver.id;

// WebSocket connections
let notificationWs = null;  // For ride offers
let locationWs = null;      // For location sharing during ride
let currentRideId = null;
let currentOfferTimeout = null;
let map, driverMarker, pickupMarker, destMarker, routeLine;

// ============================================
// WEBSOCKET NOTIFICATION SYSTEM
// ============================================

function connectNotificationWebSocket() {
    if (notificationWs) {
        notificationWs.close();
    }
    
    notificationWs = new WebSocket(`${WS_URL}/ws/notifications/${DRIVER_ID}`);
    
    notificationWs.onopen = function() {
        console.log('✅ Connected to notification system');
        showToast('Connected to ride matching system', 'success');
        
        // Send heartbeat every 30 seconds
        setInterval(() => {
            if (notificationWs.readyState === WebSocket.OPEN) {
                notificationWs.send(JSON.stringify({ type: 'heartbeat' }));
            }
        }, 30000);
    };
    
    notificationWs.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log('📨 Received notification:', data);
        
        switch(data.type) {
            case 'ride_offer':
                handleRideOffer(data);
                break;
                
            case 'offer_expired':
                handleOfferExpired(data);
                break;
                
            case 'heartbeat_ack':
                // Server acknowledged heartbeat
                break;
                
            default:
                console.log('Unknown notification type:', data.type);
        }
    };
    
    notificationWs.onerror = function(error) {
        console.error('❌ WebSocket error:', error);
        showToast('Connection error - trying to reconnect...', 'warning');
    };
    
    notificationWs.onclose = function() {
        console.log('❌ Disconnected from notification system');
        showToast('Disconnected - will reconnect in 5 seconds', 'warning');
        
        // Auto-reconnect after 5 seconds
        setTimeout(() => {
            const onlineToggle = document.getElementById('onlineToggle');
            if (onlineToggle && onlineToggle.checked) {
                connectNotificationWebSocket();
            }
        }, 5000);
    };
}

// ============================================
// RIDE OFFER HANDLING
// ============================================

function handleRideOffer(data) {
    console.log('🎯 New ride offer:', data);
    
    // Clear any existing offer
    clearCurrentOffer();
    
    // Show offer in UI
    displayRideOffer(data);
    
    // Start countdown timer
    startOfferCountdown(data.expires_in);
    
    // Auto-decline after timeout
    currentOfferTimeout = setTimeout(() => {
        console.log('⏰ Offer timed out');
        clearCurrentOffer();
        showToast('Ride offer expired', 'info');
    }, data.expires_in * 1000);
}

function displayRideOffer(offer) {
    const container = document.getElementById('rideOfferContainer');
    
    // Show pickup and destination on map
    if (offer.pickup_lat && offer.pickup_lng) {
        const pickupLatLng = [offer.pickup_lat, offer.pickup_lng];
        
        if (pickupMarker) map.removeLayer(pickupMarker);
        pickupMarker = L.marker(pickupLatLng, {
            icon: L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41]
            })
        }).addTo(map).bindPopup('Pickup Location').openPopup();
        
        map.setView(pickupLatLng, 14);
    }
    
    container.innerHTML = `
        <div class="card border-primary mb-4 shadow-lg">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">
                    <i class="fas fa-bell"></i> New Ride Request
                </h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-8">
                        <h6 class="text-primary">Ride #${offer.ride_id}</h6>
                        <p class="mb-2">
                            <i class="fas fa-map-marker-alt text-success"></i>
                            <strong>Pickup:</strong> ${offer.pickup_location || 'Getting location...'}
                        </p>
                        <p class="mb-2">
                            <i class="fas fa-map-marker-alt text-danger"></i>
                            <strong>Dropoff:</strong> ${offer.dropoff_location || 'Loading...'}
                        </p>
                        ${offer.fare ? `<p class="mb-2"><strong>Estimated Fare:</strong> $${offer.fare.toFixed(2)}</p>` : ''}
                        <p class="mb-0">
                            <strong>Time remaining:</strong> 
                            <span id="offerCountdown" class="badge bg-warning text-dark">${offer.expires_in}s</span>
                        </p>
                    </div>
                    <div class="col-md-4 text-end">
                        <button 
                            class="btn btn-success btn-lg mb-2 w-100" 
                            onclick="acceptCurrentOffer(${offer.ride_id})"
                        >
                            <i class="fas fa-check"></i> Accept
                        </button>
                        <button 
                            class="btn btn-outline-danger w-100" 
                            onclick="declineCurrentOffer(${offer.ride_id})"
                        >
                            <i class="fas fa-times"></i> Decline
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Show audio/visual alert
    playNotificationSound();
}

function startOfferCountdown(seconds) {
    let remaining = seconds;
    const countdownElement = document.getElementById('offerCountdown');
    
    const intervalId = setInterval(() => {
        remaining--;
        if (countdownElement) {
            countdownElement.textContent = `${remaining}s`;
            
            // Change color as time runs out
            if (remaining <= 5) {
                countdownElement.className = 'badge bg-danger';
            }
        }
        
        if (remaining <= 0) {
            clearInterval(intervalId);
        }
    }, 1000);
}

function handleOfferExpired(data) {
    console.log('⏰ Offer expired:', data.ride_id);
    clearCurrentOffer();
}

function clearCurrentOffer() {
    const container = document.getElementById('rideOfferContainer');
    container.innerHTML = '';
    
    if (currentOfferTimeout) {
        clearTimeout(currentOfferTimeout);
        currentOfferTimeout = null;
    }
    
    // Remove pickup marker
    if (pickupMarker) {
        map.removeLayer(pickupMarker);
        pickupMarker = null;
    }
}

// ============================================
// ACCEPT / DECLINE ACTIONS
// ============================================

async function acceptCurrentOffer(rideId) {
    try {
        const response = await fetch(`${API_URL}/rides/${rideId}/accept`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ driver_id: DRIVER_ID })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showToast('✅ Ride accepted!', 'success');
            clearCurrentOffer();
            updateCurrentRide(result.ride);
            
            // Turn off availability
            document.getElementById('onlineToggle').checked = false;
            document.getElementById('statusLabel').textContent = 'On Ride';
            document.getElementById('statusLabel').className = 'form-check-label text-info';
        } else {
            showToast(`❌ ${result.detail || result.message}`, 'danger');
            clearCurrentOffer();
        }
    } catch (error) {
        console.error('Error accepting ride:', error);
        showToast('Error accepting ride', 'danger');
    }
}

async function declineCurrentOffer(rideId) {
    try {
        const response = await fetch(`${API_URL}/rides/${rideId}/decline`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ driver_id: DRIVER_ID })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showToast('Ride declined - looking for another match', 'info');
            clearCurrentOffer();
        } else {
            showToast(`Error declining: ${result.detail || result.message}`, 'warning');
            clearCurrentOffer();
        }
    } catch (error) {
        console.error('Error declining ride:', error);
        clearCurrentOffer();
    }
}

// ============================================
// CURRENT RIDE MANAGEMENT
// ============================================

function updateCurrentRide(ride) {
    const container = document.getElementById('currentRide');
    
    if (!ride || ride.status === 'completed') {
        container.innerHTML = `
            <div class="card-body">
                <p class="text-muted">No active ride</p>
                <p class="small">You will be notified when a new ride is offered</p>
            </div>
        `;
        
        // Clean up map
        if (pickupMarker) map.removeLayer(pickupMarker);
        if (destMarker) map.removeLayer(destMarker);
        if (routeLine) map.removeLayer(routeLine);
        
        // Close location WebSocket
        if (locationWs) {
            locationWs.close();
            locationWs = null;
        }
        
        currentRideId = null;
        return;
    }
    
    currentRideId = ride.id;
    
    container.innerHTML = `
        <div class="card-body">
            <h5 class="card-title">Ride #${ride.id}</h5>
            <div class="row">
                <div class="col-md-8">
                    <p><strong>Pickup:</strong> ${ride.start_location}</p>
                    <p><strong>Dropoff:</strong> ${ride.end_location}</p>
                    <p><strong>Rider:</strong> ${ride.rider ? ride.rider.username : 'User #' + ride.rider_id}</p>
                    <p><strong>Status:</strong> <span class="badge bg-info">${ride.status}</span></p>
                </div>
                <div class="col-md-4 text-end">
                    ${ride.status === 'accepted' ? `
                        <button class="btn btn-primary mb-2 w-100" onclick="startRide(${ride.id})">
                            <i class="fas fa-play"></i> Start Ride
                        </button>
                    ` : ''}
                    ${ride.status === 'in_progress' ? `
                        <button class="btn btn-success w-100" onclick="completeRide(${ride.id})">
                            <i class="fas fa-check"></i> Complete Ride
                        </button>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
    
    // Show on map
    showRideOnMap(ride);
    
    // Connect location WebSocket for real-time sharing
    connectLocationWebSocket(ride.id);
}

function showRideOnMap(ride) {
    // Clear existing markers
    if (pickupMarker) map.removeLayer(pickupMarker);
    if (destMarker) map.removeLayer(destMarker);
    if (routeLine) map.removeLayer(routeLine);
    
    const pickupLatLng = [ride.start_lat, ride.start_lng];
    const destLatLng = [ride.end_lat, ride.end_lng];
    
    // Add markers
    pickupMarker = L.marker(pickupLatLng, {
        icon: L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41]
        })
    }).addTo(map).bindPopup('Pickup');
    
    destMarker = L.marker(destLatLng, {
        icon: L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41]
        })
    }).addTo(map).bindPopup('Destination');
    
    // Draw route
    routeLine = L.polyline([pickupLatLng, destLatLng], {
        color: 'purple',
        weight: 5,
        opacity: 0.7,
        dashArray: '10,10'
    }).addTo(map);
    
    // Fit bounds
    map.fitBounds([pickupLatLng, destLatLng]);
}

function connectLocationWebSocket(rideId) {
    if (locationWs) {
        locationWs.close();
    }
    
    locationWs = new WebSocket(`${WS_URL}/ws/ride/${rideId}/driver`);
    
    locationWs.onopen = function() {
        console.log('✅ Connected to location sharing');
        
        // Send location every 3 seconds
        const locationInterval = setInterval(() => {
            if (locationWs.readyState !== WebSocket.OPEN) {
                clearInterval(locationInterval);
                return;
            }
            
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(position => {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    
                    locationWs.send(JSON.stringify({ latitude: lat, longitude: lng }));
                    
                    // Update driver marker
                    if (driverMarker) {
                        driverMarker.setLatLng([lat, lng]);
                    } else {
                        driverMarker = L.marker([lat, lng], {
                            icon: L.icon({
                                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
                                iconSize: [25, 41],
                                iconAnchor: [12, 41]
                            })
                        }).addTo(map).bindPopup('You');
                    }
                });
            }
        }, 3000);
    };
}

// ============================================
// RIDE ACTIONS
// ============================================

async function startRide(rideId) {
    try {
        const response = await fetch(`${API_URL}/rides/${rideId}/start`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast('Ride started!', 'success');
            updateCurrentRide(result.ride);
        }
    } catch (error) {
        console.error('Error starting ride:', error);
        showToast('Error starting ride', 'danger');
    }
}

async function completeRide(rideId) {
    const fare = (Math.random() * 40 + 10).toFixed(2);
    
    try {
        const response = await fetch(`${API_URL}/rides/${rideId}/complete`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fare: parseFloat(fare) })
        });
        
        if (response.ok) {
            showToast(`Ride completed! Earned $${fare}`, 'success');
            updateCurrentRide(null);
            
            // Turn back online
            document.getElementById('onlineToggle').checked = true;
            document.getElementById('statusLabel').textContent = 'Online';
            document.getElementById('statusLabel').className = 'form-check-label status-online';
        }
    } catch (error) {
        console.error('Error completing ride:', error);
        showToast('Error completing ride', 'danger');
    }
}

// ============================================
// ONLINE/OFFLINE TOGGLE
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize map
    map = L.map('map').setView([12.9716, 77.5946], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
    }).addTo(map);
    
    // Get driver's location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(position => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            
            driverMarker = L.marker([lat, lng], {
                icon: L.icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41]
                })
            }).addTo(map).bindPopup('You').openPopup();
            
            map.setView([lat, lng], 15);
            
            // Update backend
            fetch(`${API_URL}/users/${DRIVER_ID}/location`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ latitude: lat, longitude: lng })
            });
        });
    }
    
    // Online toggle
    const onlineToggle = document.getElementById('onlineToggle');
    const statusLabel = document.getElementById('statusLabel');
    
    onlineToggle.addEventListener('change', function() {
        if (this.checked) {
            // Go online
            fetch(`${API_URL}/users/${DRIVER_ID}/availability`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ availability: true })
            }).then(() => {
                statusLabel.textContent = 'Online';
                statusLabel.className = 'form-check-label status-online';
                showToast('You are now online!', 'success');
                
                // Connect to notification WebSocket
                connectNotificationWebSocket();
            });
        } else {
            // Go offline
            fetch(`${API_URL}/users/${DRIVER_ID}/availability`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ availability: false })
            }).then(() => {
                statusLabel.textContent = 'Offline';
                statusLabel.className = 'form-check-label status-offline';
                showToast('You are now offline', 'info');
                
                // Disconnect WebSocket
                if (notificationWs) {
                    notificationWs.close();
                }
            });
        }
    });
    
    // Check for existing active ride
    checkActiveRide();
});

// ============================================
// UTILITY FUNCTIONS
// ============================================

async function checkActiveRide() {
    try {
        const response = await fetch(`${API_URL}/rides?driver_id=${DRIVER_ID}&status=accepted`);
        if (response.ok) {
            const rides = await response.json();
            if (rides.length > 0) {
                updateCurrentRide(rides[0]);
            }
        }
    } catch (error) {
        console.error('Error checking active ride:', error);
    }
}

function playNotificationSound() {
    // Play browser notification sound
    const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIGWm98OScTgwOUKrk87hlGwU=');
    audio.play().catch(err => console.log('Could not play sound:', err));
}

function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'danger' ? 'danger' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'info'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    setTimeout(() => toast.remove(), 5000);
}

function logout() {
    if (notificationWs) notificationWs.close();
    if (locationWs) locationWs.close();
    localStorage.removeItem('currentUser');
    window.location.href = 'login.html';
}
