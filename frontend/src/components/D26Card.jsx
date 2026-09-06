function D26Card() {
    const d26 = 62.5

    return (
        <div className="mt-6 rounded-xl border border-slate-800 bg-slate-950 p-4">
            <p className="text-sm text-slate-400">
                D26 Isotherm Depth
            </p>

            <div className="mt-2 flex items-baseline gap-2">
                <span className="text-3xl font-bold text-cyan-400">
                    {d26}
                </span>

                <span className="text-sm text-slate-400">
                    meters
                </span>
            </div>

            <p className="mt-2 text-xs text-slate-500">
                Depth where temperature reaches 26°C
            </p>
        </div>
    )
}

export default D26Card