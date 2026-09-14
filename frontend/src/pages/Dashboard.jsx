import { useEffect, useState } from "react"
import Header from "../components/Header"
import MapViewer from "../components/MapViewer"
import DepthSlider from "../components/DepthSlider"
import ProfileChart from "../components/ProfileChart"
import D26Card from "../components/D26Card"
import { getProfile, getSlice } from "../services/apiService"

function Dashboard() {
    const [inputDate, setInputDate] = useState("2023-01-15")
    const [activeDate, setActiveDate] = useState("2023-01-15")
    const [isPredicting, setIsPredicting] = useState(false)

    const [selectedLocation, setSelectedLocation] = useState(null)
    const [profileData, setProfileData] = useState(null)
    const [sliceData, setSliceData] = useState(null)
    const [depthIndex, setDepthIndex] = useState(0)
    const [profileLoading, setProfileLoading] = useState(false)
    const [sliceLoading, setSliceLoading] = useState(false)
    const [error, setError] = useState(null)

    // Local state for editable coordinates
    const [latInput, setLatInput] = useState("")
    const [lngInput, setLngInput] = useState("")

    // Sync input fields when user clicks map
    useEffect(() => {
        if (selectedLocation) {
            setLatInput(selectedLocation.latitude.toFixed(2))
            setLngInput(selectedLocation.longitude.toFixed(2))
        }
    }, [selectedLocation])

    const handleCoordSubmit = () => {
        const lat = parseFloat(latInput)
        const lng = parseFloat(lngInput)
        if (!isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
            setSelectedLocation({ latitude: lat, longitude: lng })
        }
    }

    const depths = [
        0, 5, 10, 20, 30,
        50, 75, 100, 125, 150,
        200, 300, 500, 700, 1000
    ]

    const handleRunModel = () => {
        setIsPredicting(true)
        setActiveDate(inputDate)
        // Simulate a delay for UI feedback
        setTimeout(() => {
            setIsPredicting(false)
        }, 2000)
    }

    // Get temperature profile when a location is selected or date changes
    useEffect(() => {
        if (!selectedLocation) {
            return
        }

        setProfileLoading(true)
        setError(null)

        getProfile(
            selectedLocation.latitude,
            selectedLocation.longitude,
            activeDate
        )
            .then((data) => {
                setProfileData({
                    ...data,
                    depths: data.depths_m,
                    temperatures: data.temperatures_c,
                    d26: data.d26_depth_m
                })
            })
            .catch((error) => {
                console.error("Profile request failed:", error)
                setError("Service unavailable. Please try again.")
            })
            .finally(() => {
                setProfileLoading(false)
            })
    }, [selectedLocation, activeDate])
    
    // Get temperature slice when depth or date changes
    useEffect(() => {
        const selectedDepth = depths[depthIndex]

        setSliceLoading(true)
        setError(null)

        getSlice(selectedDepth, activeDate)
            .then((data) => {
                setSliceData(data.temperatures_2d)
            })
            .catch((error) => {
                console.error("Slice request failed:", error)
                setError("Service unavailable. Please try again.")
            })
            .finally(() => {
                setSliceLoading(false)
            })
    }, [depthIndex, activeDate])

    return (
        <div className="min-h-screen bg-[#f7f7f5] font-sans text-[#1b0624] selection:bg-[#1b0624] selection:text-white pb-20 relative">
            
            {/* FULL SCREEN LOADING OVERLAY */}
            {isPredicting && (
                <div className="fixed inset-0 z-[9999] bg-[#f7f7f5]/80 backdrop-blur-sm flex items-center justify-center">
                    <div className="bg-white px-12 py-10 rounded-[32px] shadow-[0_8px_32px_rgba(0,0,0,0.06)] border border-black/5 flex flex-col items-center gap-6">
                        <div className="w-10 h-10 rounded-full border-[3px] border-black/5 border-t-[#1b0624] animate-spin"></div>
                        <p className="text-[14px] font-bold tracking-widest uppercase text-[#1b0624]">
                            Loading...
                        </p>
                        <p className="text-[12px] font-light text-[#1b0624]/60 max-w-[200px] text-center leading-relaxed">
                            Generating deep ocean temperature predictions.
                        </p>
                    </div>
                </div>
            )}

            <Header 
                selectedDate={inputDate} 
                onDateChange={setInputDate} 
                onRunModel={handleRunModel} 
                isPredicting={isPredicting}
            />

            <main className="p-6 md:px-12 md:py-16 max-w-[1600px] mx-auto">
                <div className="mb-12 max-w-[800px]">
                    <h2 className="text-[48px] md:text-[56px] font-normal tracking-[-0.04em] leading-[1.05] text-[#1b0624] mb-4">
                        Telemetry Console
                    </h2>
                    <p className="text-[20px] font-light text-[#1b0624]/60 leading-relaxed">
                        Select a geographic coordinate to extract vertical temperature profiles and track the D26 isotherm across the global grid.
                    </p>
                </div>

                <div className="flex flex-col xl:flex-row gap-8">

                    {/* MAP & DEPTH SLIDER */}
                    <div className="flex-1 flex flex-col gap-6">
                        <section className="min-h-[600px] xl:min-h-[700px] rounded-[32px] border border-black/5 bg-white shadow-[0_8px_32px_rgba(0,0,0,0.04)] overflow-hidden flex flex-col relative">
                            {sliceLoading && (
                                <div className="absolute top-6 left-6 z-[2000] px-4 py-2 rounded-full bg-white/90 backdrop-blur-md shadow-sm border border-black/5 text-[11px] uppercase tracking-widest text-[#1b0624]/60 font-medium">
                                    Loading temperature grid...
                                </div>
                            )}

                            <div className="flex-1 relative">
                                <MapViewer
                                    onLocationSelect={setSelectedLocation}
                                    depthIndex={depthIndex}
                                    sliceData={sliceData}
                                    selectedLocation={selectedLocation}
                                />
                            </div>
                        </section>

                        {/* BOTTOM CONTROL: DEPTH SLIDER */}
                        <div className="w-full">
                            <DepthSlider
                                depthIndex={depthIndex}
                                setDepthIndex={setDepthIndex}
                            />
                        </div>
                    </div>

                    {/* RIGHT SIDEBAR: ANALYSIS PANEL */}
                    <aside className="w-full xl:w-[480px] flex flex-col gap-6">
                        
                        {error && (
                            <div className="rounded-[24px] border border-red-500/20 bg-red-50 p-6 flex items-center gap-3">
                                <span className="text-red-500">⚠</span>
                                <p className="text-[14px] text-red-600 font-light">
                                    {error}
                                </p>
                            </div>
                        )}

                        {/* SELECTED LOCATION - EDITABLE */}
                        <div className="rounded-[24px] border border-black/5 bg-white shadow-[0_4px_24px_rgba(0,0,0,0.03)] p-8">
                            <p className="text-[11px] uppercase tracking-widest text-[#1b0624]/40 font-medium mb-6">
                                Selected Coordinate
                            </p>

                            <div className="grid grid-cols-2 gap-8">
                                <div>
                                    <label className="block text-[12px] text-[#1b0624]/40 mb-2">Latitude</label>
                                    <div className="flex items-center gap-1">
                                        <input
                                            type="text"
                                            value={latInput}
                                            onChange={(e) => setLatInput(e.target.value)}
                                            onBlur={handleCoordSubmit}
                                            onKeyDown={(e) => e.key === 'Enter' && handleCoordSubmit()}
                                            placeholder="0.00"
                                            className="w-full bg-transparent text-[24px] font-light tracking-tight text-[#1b0624] border-b border-transparent focus:border-black/10 outline-none pb-1 transition-colors"
                                        />
                                        <span className="text-[24px] font-light text-[#1b0624]/40">°</span>
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-[12px] text-[#1b0624]/40 mb-2">Longitude</label>
                                    <div className="flex items-center gap-1">
                                        <input
                                            type="text"
                                            value={lngInput}
                                            onChange={(e) => setLngInput(e.target.value)}
                                            onBlur={handleCoordSubmit}
                                            onKeyDown={(e) => e.key === 'Enter' && handleCoordSubmit()}
                                            placeholder="0.00"
                                            className="w-full bg-transparent text-[24px] font-light tracking-tight text-[#1b0624] border-b border-transparent focus:border-black/10 outline-none pb-1 transition-colors"
                                        />
                                        <span className="text-[24px] font-light text-[#1b0624]/40">°</span>
                                    </div>
                                </div>
                            </div>
                            
                            {!selectedLocation && (
                                <p className="mt-4 text-[12px] text-[#1b0624]/40 italic">
                                    Click anywhere on the map or type coordinates to begin.
                                </p>
                            )}
                        </div>

                        {/* PROFILE CHART */}
                        <div>
                            <ProfileChart
                                location={selectedLocation}
                                profileData={profileData}
                            />
                        </div>

                        {/* D26 */}
                        <div className="mt-auto">
                            <D26Card d26={profileData?.d26} />
                        </div>

                    </aside>
                </div>
            </main>
        </div>
    )
}

export default Dashboard