import { useMemo, useState } from "react"
import {
    MapContainer,
    TileLayer,
    useMapEvents,
    Marker,
    ImageOverlay,
} from "react-leaflet"
import "leaflet/dist/leaflet.css"

function MapClickHandler({ onLocationSelect }) {
    useMapEvents({
        click(event) {
            const { lat, lng } = event.latlng

            onLocationSelect({
                latitude: lat,
                longitude: lng,
            })
        },
    })

    return null
}

function TemperatureOverlay({ sliceData }) {
    const imageUrl = useMemo(() => {
        if (
            !sliceData ||
            !sliceData.latitudes ||
            !sliceData.longitudes ||
            !sliceData.temperatures_2d
        ) {
            return null
        }

        const latitudes = sliceData.latitudes
        const longitudes = sliceData.longitudes
        const temperatures = sliceData.temperatures_2d

        const rows = latitudes.length
        const cols = longitudes.length

        const canvas = document.createElement("canvas")

        canvas.width = cols
        canvas.height = rows

        const ctx = canvas.getContext("2d")

        function getColor(temperature) {
            if (
                temperature === null ||
                temperature === undefined
            ) {
                return null
            }

            const minTemp = 8
            const maxTemp = 30

            const value = Math.max(
                0,
                Math.min(
                    1,
                    (temperature - minTemp) /
                    (maxTemp - minTemp)
                )
            )

            if (value < 0.5) {
                const ratio = value / 0.5

                const r = Math.round(
                    34 + ratio * (250 - 34)
                )

                const g = Math.round(
                    211 + ratio * (204 - 211)
                )

                const b = Math.round(
                    238 + ratio * (21 - 238)
                )

                return `rgb(${r}, ${g}, ${b})`
            }

            const ratio = (value - 0.5) / 0.5

            const r = Math.round(
                250 + ratio * (239 - 250)
            )

            const g = Math.round(
                204 + ratio * (68 - 204)
            )

            const b = Math.round(
                21 + ratio * (68 - 21)
            )

            return `rgb(${r}, ${g}, ${b})`
        }

        for (let i = 0; i < rows; i++) {
            for (let j = 0; j < cols; j++) {
                const temperature =
                    temperatures[i]?.[j]

                const color = getColor(temperature)

                if (!color) {
                    continue
                }

                // Latitude increases from south to north.
                // Canvas starts from top, so flip the row.
                const y = rows - 1 - i

                ctx.fillStyle = color
                ctx.fillRect(j, y, 1, 1)
            }
        }

        return canvas.toDataURL("image/png")
    }, [sliceData])

    if (!imageUrl) {
        return null
    }

    const bounds = [
        [5, 45],
        [30, 105],
    ]

    return (
        <ImageOverlay
            url={imageUrl}
            bounds={bounds}
            opacity={0.65}
            interactive={false}
        />
    )
}

function MapViewer({
    onLocationSelect,
    depthIndex,
    sliceData,
}) {
    const [selectedPosition, setSelectedPosition] =
        useState(null)

    const oceanBounds = [
        [5, 45],
        [30, 105],
    ]

    function handleLocationSelect(location) {
        setSelectedPosition([
            location.latitude,
            location.longitude,
        ])

        onLocationSelect(location)
    }

    return (
        <div className="relative h-[500px] w-full overflow-hidden rounded-xl">
            <MapContainer
                bounds={oceanBounds}
                scrollWheelZoom={true}
                className="h-full w-full"
            >
                <MapClickHandler
                    onLocationSelect={handleLocationSelect}
                />

                {selectedPosition && (
                    <Marker position={selectedPosition} />
                )}

                <TileLayer
                    attribution="&copy; OpenStreetMap contributors"
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <TemperatureOverlay
                    sliceData={sliceData}
                />
            </MapContainer>

            <div className="absolute bottom-4 right-4 z-[1000] w-52 rounded-lg border border-slate-700 bg-slate-950/90 p-3 shadow-lg">
                <div className="mb-2 text-xs font-semibold text-white">
                    Temperature (°C)
                </div>

                <div className="h-3 w-full rounded-full bg-gradient-to-r from-cyan-400 via-yellow-300 to-red-500" />

                <div className="mt-1 flex justify-between text-xs text-slate-300">
                    <span>8°C</span>
                    <span>18°C</span>
                    <span>30°C</span>
                </div>
            </div>
        </div>
    )
}

export default MapViewer