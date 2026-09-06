import { useEffect, useState } from "react"
import Header from "../components/Header"
import MapViewer from "../components/MapViewer"
import DepthSlider from "../components/DepthSlider"
import ProfileChart from "../components/ProfileChart"
import D26Card from "../components/D26Card"
import { getProfile, getSlice } from "../services/apiService"

function Dashboard() {
    const [selectedLocation, setSelectedLocation] = useState(null)
    const [profileData, setProfileData] = useState(null)
    const [sliceData, setSliceData] = useState(null)
    const [depthIndex, setDepthIndex] = useState(0)
    const [profileLoading, setProfileLoading] = useState(false)
    const [sliceLoading, setSliceLoading] = useState(false)
    const [error, setError] = useState(null)

    const depths = [
        0, 5, 10, 20, 30,
        50, 75, 100, 125, 150,
        200, 300, 500, 700, 1000
    ]

    // Get temperature profile when a location is selected
    useEffect(() => {
        if (!selectedLocation) {
            return
        }

        setProfileLoading(true)
        setError(null)

        getProfile(
            selectedLocation.latitude,
            selectedLocation.longitude
        )
            .then((data) => {
                setProfileData(data)
            })
            .catch((error) => {
                console.error("Profile request failed:", error)
                setError("Service unavailable. Please try again.")
            })
            .finally(() => {
                setProfileLoading(false)
            })
    }, [selectedLocation])
    // Get temperature slice when depth changes
    useEffect(() => {
        const selectedDepth = depths[depthIndex]

        setSliceLoading(true)
        setError(null)

        getSlice(selectedDepth)
            .then((data) => {
                setSliceData(data)
            })
            .catch((error) => {
                console.error("Slice request failed:", error)
                setError("Service unavailable. Please try again.")
            })
            .finally(() => {
                setSliceLoading(false)
            })
    }, [depthIndex])

    return (
        <div className="min-h-screen bg-slate-950">
            <Header />

            <main className="p-6">
                <div className="grid grid-cols-1 gap-6 md:grid-cols-3">

                    {/* MAP */}
                    <section className="min-h-[600px] rounded-2xl border border-slate-800 bg-slate-900 md:col-span-2">

                        <div className="p-5">
                            <h2 className="text-lg font-semibold text-white">
                                Ocean Temperature Map
                            </h2>

                            <p className="mt-1 text-sm text-slate-400">
                                North Indian Ocean
                            </p>
                        </div>

                        {sliceLoading && (
                            <p className="mb-2 text-sm text-cyan-400">
                                Loading temperature map...
                            </p>
                        )}

                        <MapViewer
                            onLocationSelect={setSelectedLocation}
                            depthIndex={depthIndex}
                            sliceData={sliceData}
                        />

                    </section>

                    {/* ANALYSIS PANEL */}
                    <aside className="rounded-2xl border border-slate-800 bg-slate-900 p-5">

                        <h2 className="text-lg font-semibold text-white">
                            Analysis
                        </h2>

                        {error && (
                            <div className="mt-4 rounded-lg border border-red-900 bg-red-950/40 p-3">
                                <p className="text-sm text-red-300">
                                    ⚠️ {error}
                                </p>
                            </div>
                        )}

                        <p className="mt-2 text-sm text-slate-400">
                            Select a location on the map to explore ocean temperature.
                        </p>

                        {/* SELECTED LOCATION */}
                        {selectedLocation && (
                            <div className="mt-6 rounded-xl border border-slate-700 bg-slate-950 p-4">

                                <p className="text-sm text-slate-400">
                                    Selected Location
                                </p>

                                <div className="mt-2 grid grid-cols-2 gap-3">

                                    <div>
                                        <p className="text-xs text-slate-500">
                                            Latitude
                                        </p>

                                        <p className="text-lg font-semibold text-white">
                                            {selectedLocation.latitude.toFixed(2)}°
                                        </p>
                                    </div>

                                    <div>
                                        <p className="text-xs text-slate-500">
                                            Longitude
                                        </p>

                                        <p className="text-lg font-semibold text-white">
                                            {selectedLocation.longitude.toFixed(2)}°
                                        </p>
                                    </div>

                                </div>
                            </div>
                        )}

                        {/* DEPTH SLIDER */}
                        <div className="mt-6">
                            <DepthSlider
                                depthIndex={depthIndex}
                                setDepthIndex={setDepthIndex}
                            />
                        </div>

                        <div className="mt-6">
                            {profileLoading && (
                                <p className="mb-2 text-sm text-cyan-400">
                                    Loading temperature profile...
                                </p>
                            )}

                            <ProfileChart
                                location={selectedLocation}
                                profileData={profileData}
                            />
                        </div>

                        {/* D26 */}
                        <div className="mt-6">
                            <D26Card />
                        </div>

                    </aside>
                </div>
            </main>
        </div>
    )
}

export default Dashboard