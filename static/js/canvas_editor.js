const canvas = document.getElementById('slotCanvas');
const ctx = canvas.getContext('2d');
const img = document.getElementById('refImage');

// State
let slots = []; // Array of arrays: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]

// Check for injected slots from template
if (window.importedSlots && Array.isArray(window.importedSlots)) {
    slots = window.importedSlots;
}

let currentPoints = []; // Temporary points for polygon drawing
let isDrawingRect = false;
let rectStart = null;
let scale = 1.0;

// Config
const modeRect = document.getElementById('modeRect');
const modePoly = document.getElementById('modePoly');
const helpText = document.getElementById('helpText');
const zoomLevelSpan = document.getElementById('zoomLevel');

let currentZoom = 1.0;

function setZoom(newZoom) {
    if (newZoom < 0.2 || newZoom > 5.0) return;
    currentZoom = newZoom;

    // Effectively zoom by controlling style width
    // Base resolution (canvas.width) remains constant, visual size changes
    canvas.style.width = (canvas.width * currentZoom) + "px";
    canvas.style.height = "auto";

    if (img) {
        img.style.width = (canvas.width * currentZoom) + "px";
        img.style.height = "auto";
    }

    if (zoomLevelSpan) zoomLevelSpan.innerText = Math.round(currentZoom * 100) + "%";
}

function zoomIn() { setZoom(currentZoom + 0.1); }
function zoomOut() { setZoom(currentZoom - 0.1); }

img.onload = function () {
    canvas.width = img.width;
    canvas.height = img.height;

    // Auto-fit Logic
    const container = document.getElementById('canvasContainer');
    const wrapper = container.parentElement; // Use wrapper for available space
    const containerW = wrapper.clientWidth - 80; // minus padding
    const containerH = wrapper.clientHeight - 80;

    const scaleW = containerW / img.width;
    const scaleH = containerH / img.height;

    // Use the smaller scale to ensure it fits entirely
    let fitScale = Math.min(scaleW, scaleH);
    if (fitScale > 1.0) fitScale = 1.0; // Don't upscale small images automatically

    setZoom(fitScale);
    draw();
    console.log("Image loaded. Slots to draw:", slots.length);
};

// Force trigger if already loaded (cached)
if (img.complete) {
    img.onload();
}

// UI Toggles
modeRect.addEventListener('change', () => {
    helpText.innerText = "Click and Drag to draw a box.";
    currentPoints = []; // reset polygon progress
});
modePoly.addEventListener('change', () => {
    helpText.innerText = "Click 4 corners to make a shape.";
});

// --- DRAW LOOP ---
function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // ctx.drawImage(img, 0, 0); // Video feed is handled by the <img> tag behind the canvas

    // Draw Saved Slots
    slots.forEach((points, i) => {
        drawPolygon(points, "#00FF00", true, i + 1);
    });

    // Draw In-Progress Polygon (Dots & Lines)
    if (currentPoints.length > 0) {
        ctx.strokeStyle = "yellow";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(currentPoints[0].x, currentPoints[0].y);
        for (let i = 1; i < currentPoints.length; i++) {
            ctx.lineTo(currentPoints[i].x, currentPoints[i].y);
        }
        ctx.stroke();

        // Draw dots at corners
        currentPoints.forEach(p => {
            ctx.fillStyle = "yellow";
            ctx.beginPath();
            ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
            ctx.fill();
        });
    }

    // Draw In-Progress Rectangle
    if (isDrawingRect && rectStart) {
        // We just visualize the rect here
    }
}

function drawPolygon(points, color, showLabel, label) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(points[0][0], points[0][1]); // x,y is stored as array in DB
    for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i][0], points[i][1]);
    }
    ctx.closePath();
    ctx.stroke();

    // Semi-transparent fill
    ctx.fillStyle = "rgba(0, 255, 0, 0.2)";
    ctx.fill();

    if (showLabel) {
        const cx = points[0][0];
        const cy = points[0][1];
        ctx.fillStyle = "white";
        ctx.font = "16px Arial";
        ctx.fillText("#" + label, cx, cy - 5);
    }
}

// --- MOUSE EVENTS ---
canvas.addEventListener('mousedown', function (e) {
    if (e.button === 2) return; // Ignore right click
    const coords = getCoords(e);

    // MODE 3: DELETE (Click to Remove)
    const modeDelete = document.getElementById('modeDelete');
    if (modeDelete && modeDelete.checked) {
        // Find if clicked inside any slot
        // Iterate backwards to click "top" one first
        for (let i = slots.length - 1; i >= 0; i--) {
            if (isPointInPoly(coords, slots[i])) {
                slots.splice(i, 1); // Remove
                draw();
                return;
            }
        }
        return;
    }

    // MODE 1: RECTANGLE (Click & Drag)
    if (modeRect.checked) {
        isDrawingRect = true;
        rectStart = coords;
    }
    // MODE 2: POLYGON (Click 4 points)
    else {
        currentPoints.push(coords);
        if (currentPoints.length === 4) {
            // Convert objects {x,y} to arrays [x,y] for consistency
            let finalShape = currentPoints.map(p => [p.x, p.y]);
            slots.push(finalShape);
            currentPoints = []; // Reset
        }
        draw();
    }
});

canvas.addEventListener('mousemove', function (e) {
    if (isDrawingRect && modeRect.checked) {
        draw(); // Refresh background
        const coords = getCoords(e);
        const w = coords.x - rectStart.x;
        const h = coords.y - rectStart.y;

        ctx.strokeStyle = "yellow";
        ctx.strokeRect(rectStart.x, rectStart.y, w, h);
    }
});

canvas.addEventListener('mouseup', function (e) {
    if (isDrawingRect && modeRect.checked) {
        const coords = getCoords(e);
        const w = coords.x - rectStart.x;
        const h = coords.y - rectStart.y;

        if (Math.abs(w) > 10 && Math.abs(h) > 10) {
            // Convert Rect to 4-point Polygon
            const x1 = rectStart.x;
            const y1 = rectStart.y;
            const x2 = rectStart.x + w;
            const y2 = rectStart.y + h;

            // Store as 4 points: TL, TR, BR, BL
            slots.push([
                [x1, y1], [x2, y1], [x2, y2], [x1, y2]
            ]);
        }
        isDrawingRect = false;
        draw();
    }
});

// Right Click to Delete
canvas.addEventListener('contextmenu', function (e) {
    e.preventDefault();
    if (slots.length > 0) {
        slots.pop(); // Remove last added
        draw();
    }
});

function getCoords(e) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    return {
        x: Math.round((e.clientX - rect.left) * scaleX),
        y: Math.round((e.clientY - rect.top) * scaleY)
    };
}

// Ray-casting algorithm for point in polygon
function isPointInPoly(pt, poly) {
    let inside = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
        const xi = poly[i][0], yi = poly[i][1];
        const xj = poly[j][0], yj = poly[j][1];
        const intersect = ((yi > pt.y) !== (yj > pt.y))
            && (pt.x < (xj - xi) * (pt.y - yi) / (yj - yi) + xi);
        if (intersect) inside = !inside;
    }
    return inside;
}

function undo() {
    slots.pop();
    draw();
}

// Initialize with saved slots if available
// We expose this so the template can call it after defining the data
window.loadSavedSlots = function (data) {
    if (data && Array.isArray(data)) {
        slots = data;
        draw();
    }
};

function saveSlots(lotId) {
    fetch('/api/save_slots', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lot_id: lotId, rects: slots })
        // Note: 'rects' now contains lists of points, not x/y/w/h
    })
        .then(res => res.json())
        .then(data => {
            alert("✅ Saved!");
            window.location.href = "/provider/dashboard";
        });
}