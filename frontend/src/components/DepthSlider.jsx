function DepthSlider({ depthIndex, setDepthIndex }) {
    const depths = [
        0, 5, 10, 20, 30,
        50, 75, 100, 125, 150,
        200, 300, 500, 700, 1000
    ]

    const selectedDepth = depths[depthIndex]

    return (
        <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">

            <div className="mb-3 flex items-center justify-between">
                <span className="text-sm text-slate-400">
                    Depth
                </span>

                <span className="text-lg font-semibold text-cyan-400">
                    {selectedDepth} m
                </span>
            </div>

            <input
                type="range"
                min="0"
                max={depths.length - 1}
                value={depthIndex}
                onChange={(event) =>
                    setDepthIndex(Number(event.target.value))
                }
                className="w-full"
            />

            <div className="mt-2 flex justify-between text-xs text-slate-500">
                <span>Surface</span>
                <span>1000 m</span>
            </div>

        </div>
    )
}

export default DepthSlider