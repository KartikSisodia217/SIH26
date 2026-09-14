import { useEffect, useState, useRef } from "react"
import {
    MapContainer,
    TileLayer,
    useMapEvents,
    useMap,
    Marker
} from "react-leaflet"
import "leaflet/dist/leaflet.css"
import L from "leaflet"

// Fix for default marker icons in React Leaflet
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
    iconRetinaUrl:
        "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
    iconUrl:
        "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
    shadowUrl:
        "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
})

// Helper component to fix map sizing issues on load
function MapResizer() {
    const map = useMap()
    useEffect(() => {
        setTimeout(() => {
            map.invalidateSize()
        }, 200)
    }, [map])
    return null
}

function MapClickHandler({ onLocationSelect }) {
    useMapEvents({
        click(e) {
            const { lat, lng } = e.latlng
            onLocationSelect({ latitude: lat, longitude: lng })
        },
    })
    return null
}

function TemperatureOverlay({ sliceData }) {
    const map = useMap()
    const canvasRef = useRef(null)
    const overlayRef = useRef(null)

    useEffect(() => {
        if (!sliceData || !sliceData.length) return

        const bounds = L.latLngBounds(
            [5, 45], // South-West corner
            [30, 105] // North-East corner
        )

        if (!canvasRef.current) {
            const canvas = document.createElement("canvas")
            canvasRef.current = canvas
        }

        const canvas = canvasRef.current
        const ctx = canvas.getContext("2d")

        // Dimensions of the slice data grid
        const height = sliceData.length
        const width = sliceData[0].length

        canvas.width = width
        canvas.height = height

        const imageData = ctx.createImageData(width, height)
        const data = imageData.data

        // Flatten and apply colors (Jet colormap approximation)
        let dataIndex = 0
        // Leaflet image overlays stretch from SW to NE. 
        // Data usually comes North to South.
        // We flip Y if necessary depending on the backend, let's keep it straight first.
        for (let i = 0; i < height; i++) {
            for (let j = 0; j < width; j++) {
                const temp = sliceData[i][j]

                if (temp === null || isNaN(temp)) {
                    // Transparent for land/no-data
                    data[dataIndex] = 0
                    data[dataIndex + 1] = 0
                    data[dataIndex + 2] = 0
                    data[dataIndex + 3] = 0
                } else {
                    // Normalize temperature between 5 and 32 for color mapping
                    const minTemp = 5
                    const maxTemp = 32
                    const norm = Math.max(0, Math.min(1, (temp - minTemp) / (maxTemp - minTemp)))

                    // Simple Jet-like colormap
                    const r = Math.max(0, Math.min(255, 255 * (1.5 - Math.abs(1 - 4 * (norm - 0.5)))))
                    const g = Math.max(0, Math.min(255, 255 * (1.5 - Math.abs(1 - 4 * (norm - 0.25)))))
                    const b = Math.max(0, Math.min(255, 255 * (1.5 - Math.abs(1 - 4 * norm))))

                    data[dataIndex] = r
                    data[dataIndex + 1] = g
                    data[dataIndex + 2] = b
                    data[dataIndex + 3] = 180 // opacity
                }
                dataIndex += 4
            }
        }

        ctx.putImageData(imageData, 0, 0)
        const imageUrl = canvas.toDataURL()

        if (overlayRef.current) {
            map.removeLayer(overlayRef.current)
        }

        overlayRef.current = L.imageOverlay(imageUrl, bounds, {
            opacity: 0.65,
            interactive: false
        }).addTo(map)

        return () => {
            // cleanup is handled on unmount, but let's leave it simple
        }
    }, [sliceData, map])

    return null
}

function MapCenterUpdater({ selectedLocation }) {
    const map = useMap()
    useEffect(() => {
        if (selectedLocation) {
            map.flyTo([selectedLocation.latitude, selectedLocation.longitude], map.getZoom(), {
                animate: true,
                duration: 0.5
            })
        }
    }, [selectedLocation, map])
    return null
}

function MapViewer({
    onLocationSelect,
    depthIndex,
    sliceData,
    selectedLocation
}) {
    // Prevent zooming way out into grey space
    const maxBounds = [
        [-60, -180],
        [80, 180]
    ]

    return (
        <div className="relative h-full w-full overflow-hidden rounded-[24px]">
            <MapContainer
                center={[17.5, 75.0]}
                zoom={5}
                minZoom={3}
                maxBounds={maxBounds}
                maxBoundsViscosity={1.0}
                style={{ height: '100%', width: '100%', backgroundColor: '#000000' }}
            >
                <MapResizer />
                <MapCenterUpdater selectedLocation={selectedLocation} />
                
                <MapClickHandler
                    onLocationSelect={onLocationSelect}
                />

                {selectedLocation && (
                    <Marker position={[selectedLocation.latitude, selectedLocation.longitude]} />
                )}

                <TileLayer
                    attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
                    url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                    noWrap={true}
                />

                <TemperatureOverlay sliceData={sliceData} />

                {/* Original detailed labels, borders, and place names */}
                <TileLayer
                    url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
                    noWrap={true}
                />
            </MapContainer>

            <div className="absolute bottom-6 right-6 z-[1000] w-64 rounded-[16px] border border-black/5 bg-white/90 backdrop-blur-md p-5 shadow-[0_8px_32px_rgba(0,0,0,0.06)] pointer-events-none select-none">
                <div className="mb-3 text-[11px] uppercase tracking-widest font-semibold text-[#1b0624]/60">
                    Temperature Profile
                </div>

                <div className="h-2 w-full rounded-full bg-gradient-to-r from-blue-500 via-yellow-400 to-red-500 opacity-90" />

                <div className="mt-3 flex justify-between text-[11px] font-mono text-[#1b0624]/50">
                    <span>8°C</span>
                    <span>18°C</span>
                    <span>30°C</span>
                </div>
            </div>
        </div>
    )
}

export default MapViewer