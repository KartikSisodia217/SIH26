function DepthSlider({ depthIndex, setDepthIndex }) {
    const depths = [0, 5, 10, 20, 30, 50, 75, 100, 125, 150, 200, 300, 500, 700, 1000]
    const selectedDepth = depths[depthIndex]

    return (
        <div className="rounded-[32px] border border-black/5 bg-white shadow-[0_4px_24px_rgba(0,0,0,0.03)] p-8">
            <div className="mb-6 flex flex-col gap-2">
                <span className="text-[11px] uppercase tracking-widest text-[#1b0624]/40 font-medium">
                    Depth Slice
                </span>
                <span className="text-[40px] font-light tracking-tight text-[#1b0624] leading-none">
                    {selectedDepth} <span className="text-[20px] text-[#1b0624]/40">m</span>
                </span>
            </div>

            <input
                type="range"
                min="0"
                max={depths.length - 1}
                value={depthIndex}
                onChange={(event) => setDepthIndex(Number(event.target.value))}
                className="w-full h-[2px] bg-black/10 rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:bg-[#1b0624] [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:shadow-[0_2px_4px_rgba(0,0,0,0.2)] focus:outline-none"
            />

            <div className="mt-4 flex justify-between text-[11px] font-medium text-[#1b0624]/40 uppercase tracking-widest">
                <span>Surface</span>
                <span>1000m</span>
            </div>
        </div>
    )
}
export default DepthSlider