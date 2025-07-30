// 3D Background with Three.js
class Background3D {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.particles = [];
        this.mouseX = 0;
        this.mouseY = 0;
        this.windowHalfX = window.innerWidth / 2;
        this.windowHalfY = window.innerHeight / 2;
        
        this.init();
        this.animate();
        this.addEventListeners();
    }
    
    init() {
        // Create scene
        this.scene = new THREE.Scene();
        
        // Create camera
        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 1, 1000);
        this.camera.position.z = 500;
        
        // Create renderer
        this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        
        // Add to DOM
        const container = document.getElementById('three-background');
        if (container) {
            container.appendChild(this.renderer.domElement);
        }
        
        // Create particles
        this.createParticles();
        
        // Create floating geometries
        this.createFloatingGeometries();
    }
    
    createParticles() {
        const particleCount = 100;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const colors = new Float32Array(particleCount * 3);
        
        const color = new THREE.Color();
        
        for (let i = 0; i < particleCount * 3; i += 3) {
            // Positions
            positions[i] = (Math.random() - 0.5) * 2000;
            positions[i + 1] = (Math.random() - 0.5) * 2000;
            positions[i + 2] = (Math.random() - 0.5) * 2000;
            
            // Colors
            const hue = Math.random() * 0.3 + 0.6; // Blue to purple range
            color.setHSL(hue, 0.7, 0.6);
            colors[i] = color.r;
            colors[i + 1] = color.g;
            colors[i + 2] = color.b;
        }
        
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        
        const material = new THREE.PointsMaterial({
            size: 3,
            vertexColors: true,
            transparent: true,
            opacity: 0.6,
            blending: THREE.AdditiveBlending
        });
        
        this.particleSystem = new THREE.Points(geometry, material);
        this.scene.add(this.particleSystem);
    }
    
    createFloatingGeometries() {
        const geometries = [
            new THREE.BoxGeometry(20, 20, 20),
            new THREE.SphereGeometry(15, 16, 16),
            new THREE.ConeGeometry(15, 30, 8),
            new THREE.TorusGeometry(15, 5, 8, 16)
        ];
        
        const materials = [
            new THREE.MeshBasicMaterial({ 
                color: 0x667eea, 
                transparent: true, 
                opacity: 0.3,
                wireframe: true 
            }),
            new THREE.MeshBasicMaterial({ 
                color: 0x764ba2, 
                transparent: true, 
                opacity: 0.3,
                wireframe: true 
            }),
            new THREE.MeshBasicMaterial({ 
                color: 0xf093fb, 
                transparent: true, 
                opacity: 0.3,
                wireframe: true 
            })
        ];
        
        for (let i = 0; i < 15; i++) {
            const geometry = geometries[Math.floor(Math.random() * geometries.length)];
            const material = materials[Math.floor(Math.random() * materials.length)];
            const mesh = new THREE.Mesh(geometry, material);
            
            mesh.position.x = (Math.random() - 0.5) * 1000;
            mesh.position.y = (Math.random() - 0.5) * 1000;
            mesh.position.z = (Math.random() - 0.5) * 1000;
            
            mesh.rotation.x = Math.random() * Math.PI;
            mesh.rotation.y = Math.random() * Math.PI;
            mesh.rotation.z = Math.random() * Math.PI;
            
            this.scene.add(mesh);
            this.particles.push(mesh);
        }
    }
    
    addEventListeners() {
        document.addEventListener('mousemove', (event) => {
            this.mouseX = (event.clientX - this.windowHalfX) * 0.5;
            this.mouseY = (event.clientY - this.windowHalfY) * 0.5;
        });
        
        window.addEventListener('resize', () => {
            this.windowHalfX = window.innerWidth / 2;
            this.windowHalfY = window.innerHeight / 2;
            
            this.camera.aspect = window.innerWidth / window.innerHeight;
            this.camera.updateProjectionMatrix();
            
            this.renderer.setSize(window.innerWidth, window.innerHeight);
        });
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        
        // Rotate particles
        if (this.particleSystem) {
            this.particleSystem.rotation.x += 0.001;
            this.particleSystem.rotation.y += 0.002;
        }
        
        // Animate floating geometries
        this.particles.forEach((particle, index) => {
            particle.rotation.x += 0.01 + index * 0.001;
            particle.rotation.y += 0.01 + index * 0.001;
            particle.position.y = Math.sin(Date.now() * 0.001 + index) * 20;
        });
        
        // Mouse interaction
        this.camera.position.x += (this.mouseX - this.camera.position.x) * 0.05;
        this.camera.position.y += (-this.mouseY - this.camera.position.y) * 0.05;
        this.camera.lookAt(this.scene.position);
        
        this.renderer.render(this.scene, this.camera);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (typeof THREE !== 'undefined') {
        new Background3D();
    }
});
