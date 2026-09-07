function Header() {
    return (
        <header className="h-16 border-b border-slate-800 bg-slate-950 px-6 flex items-center justify-between">

            <div className="flex items-center gap-3">
                <span className="text-2xl">🌊</span>

                <div>
                    <h1 className="text-lg font-semibold text-white">
                        OceanEmbed
                    </h1>
                    <p className="text-xs text-slate-400">
                        North Indian Ocean Visualization
                    </p>
                </div>
            </div>

            <div className="text-sm text-slate-400">
                3D Ocean Temperature
            </div>

        </header>
    )
}

export default Header