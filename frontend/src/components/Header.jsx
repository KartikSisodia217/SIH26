function Header({ selectedDate, onDateChange, onRunModel, isPredicting }) {
    return (
        <header className="h-[88px] border-b border-black/5 bg-[#f7f7f5] px-6 md:px-12 flex items-center justify-between sticky top-0 z-50">
            <div className="flex items-center gap-4">
                <span className="text-[28px] text-[#1b0624]">✱</span>
                <div>
                    <h1 className="text-[20px] font-bold tracking-tight text-[#1b0624]">
                        OceanEmbed
                    </h1>
                    <div className="text-[11px] font-medium text-[#1b0624]/50 tracking-widest uppercase mt-0.5">
                        Copernicus Global Grid
                    </div>
                </div>
            </div>
            
            <div className="flex items-center gap-6">
                <div className="flex items-center gap-3">
                    <label htmlFor="date-picker" className="text-[11px] uppercase tracking-widest text-[#1b0624]/60 font-medium">
                        Prediction Date
                    </label>
                    <input 
                        id="date-picker"
                        type="date" 
                        value={selectedDate} 
                        onChange={(e) => onDateChange(e.target.value)}
                        className="bg-white border border-black/10 rounded-full px-4 py-2 text-[14px] text-[#1b0624] font-mono outline-none focus:border-[#1b0624]/30 shadow-sm"
                    />
                </div>
                
                <button 
                    onClick={onRunModel}
                    disabled={isPredicting}
                    className="bg-[#1b0624] hover:bg-[#2d0a3d] text-white px-8 py-3 rounded-full text-[13px] font-bold tracking-wide uppercase disabled:opacity-50 transition-all shadow-md"
                >
                    {isPredicting ? "Running..." : "Run Model"}
                </button>
            </div>
        </header>
    )
}
export default Header