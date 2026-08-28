import React, { useRef, useEffect } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";

export default function PointsVisualization() {
  const mountRef = useRef(null);
  const hoverTimeoutRef = useRef(null); // Ref to store hover timeout
  const sphereMeshes = useRef([]); // Ref to store the sphere meshes

  useEffect(() => {
    // Scene setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(400, 400);
    mountRef.current.appendChild(renderer.domElement);

    // OrbitControls setup
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true; // an animation loop is required when either damping or auto-rotation are enabled
    controls.dampingFactor = 0.25;
    controls.screenSpacePanning = false;
    controls.maxPolarAngle = Math.PI / 2;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);
    const pointLight = new THREE.PointLight(0xffffff, 1);
    camera.add(pointLight);
    scene.add(camera);

    // Create gradient texture (canvas)
    // Gradient texture using canvas
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    canvas.width = 64; // Texture size
    canvas.height = 64; // Texture size
    const gradient = ctx.createLinearGradient(0, 0, 64, 64);
    gradient.addColorStop(0, "blue"); // Start color
    gradient.addColorStop(1, "red"); // End color
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 64, 64);
    const texture = new THREE.CanvasTexture(canvas);

    // Sphere material with gradient texture
    const material = new THREE.MeshBasicMaterial({ map: texture });

    // Raycaster for mouse interaction
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    // Axis lines setup
    const axes = new THREE.AxesHelper(5);
    axes.material.depthTest = false; // Prevents the axes from being occluded by the points
    axes.renderOrder = 1; // Renders after the points
    scene.add(axes);

    // Assuming you have an array of 3D points called `data`
    const data = [
      { x: 1, y: 1, z: 1 },
      { x: 2, y: 1, z: 1 },
      { x: 3, y: 1, z: 1 },
      { x: 1, y: 1, z: 4 },
    ];

    // for (let i = 0; i < data.length; i++) {
    //   // vertices.push(data[i].x, data[i].y, data[i].z);

    //   // color.set(Math.random() * 0xffffff);
    //   // colors.push(color.r, color.g, color.b);

    //   const geometry = new THREE.SphereGeometry(0.1);
    //   const sphere = new THREE.Mesh(geometry, material);
    //   sphere.position.set(data[i].x, data[i].y, data[i].z);
    //   scene.add(sphere);
    // }
    sphereMeshes.current = data.map((point) => {
      const geometry = new THREE.SphereGeometry(0.1, 32, 32);
      const sphereMesh = new THREE.Mesh(geometry, material);
      sphereMesh.position.set(point.x, point.y, point.z);
      scene.add(sphereMesh);
      return sphereMesh;
    });

    // pointsGeometry.setAttribute(
    //   "position",
    //   new THREE.Float32BufferAttribute(vertices, 3)
    // );

    // pointsGeometry.setAttribute(
    //   "color",
    //   new THREE.Float32BufferAttribute(colors, 3)
    // );

    // const points = new THREE.Points(pointsGeometry, pointsMaterial);
    // scene.add(points);

    camera.position.z = 5;

    function onClick(event) {
      // Calculate mouse position in normalized device coordinates (-1 to +1) for both components
      const bounds = mountRef.current.getBoundingClientRect();
      mouse.x = ((event.clientX - bounds.left) / 400) * 2 - 1;
      mouse.y = -((event.clientY - bounds.top) / 400) * 2 + 1;

      // Update the picking ray with the camera and mouse position
      raycaster.setFromCamera(mouse, camera);

      // Calculate objects intersecting the picking ray
      const intersects = raycaster.intersectObjects(sphereMeshes.current);

      if (intersects.length > 0) {
        // Handle the bounce effect here
        // For instance, you could update the vertices of the geometry and re-upload it to the GPU
      }
    }

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      controls.update(); // only required if controls.enableDamping = true, or if controls.autoRotate = true
      renderer.render(scene, camera);
    };

    const onHover = () => {
      // Trigger your event here
      // console.log("Hover event triggered on: ", intersectedObject);
    };

    const onMouseMove = (event) => {
      // Calculate mouse position in normalized device coordinates (-1 to +1) for
      const bounds = mountRef.current.getBoundingClientRect();

      mouse.x = ((event.clientX - bounds.left) / 400) * 2 - 1;
      mouse.y = -((event.clientY - bounds.top) / 400) * 2 + 1;
      // console.log({x: mouse.x, y:mouse.y})

      // Update the picking ray with the camera and mouse position
      raycaster.setFromCamera(mouse, camera);

      // Calculate objects intersecting the picking ray, only considering the spheres
      const intersects = raycaster.intersectObjects(sphereMeshes.current);

      // Clear the previous timeout if any
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
        hoverTimeoutRef.current = null;
      }

      if (intersects.length > 0) {
        // onHover("another");
        onHover(intersects[0].object);
        // Set a timeout to trigger the event after 500ms
        hoverTimeoutRef.current = setTimeout(
          () => onHover(intersects[0].object),
          500,
        );
      }
    };
    // Add event listener for mouse move
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("click", onClick);

    // Handle window resize
    window.addEventListener("resize", () => {
      renderer.setSize(400, 400);
      camera.aspect = 1;
      camera.updateProjectionMatrix();
    });
    animate();

    return () => {
      // eslint-disable-next-line react-hooks/exhaustive-deps
      mountRef.current.removeChild(renderer.domElement);
      window.removeEventListener("mousemove", onMouseMove);
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, []);

  return <div ref={mountRef} />;
}
