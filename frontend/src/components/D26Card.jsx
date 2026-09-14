function D26Card({ d26 }) {
    const displayValue = d26 !== undefined && d26 !== null ? d26 : '-';

    return (
        <div className="rounded-[24px] border border-black/5 bg-white shadow-[0_4px_24px_rgba(0,0,0,0.03)] p-8">
            <p className="text-[11px] uppercase tracking-widest text-[#1b0624]/40 font-medium mb-6">
                D26 Isotherm
            </p>

            <div className="flex items-baseline gap-2 mb-4">
                <span className="text-[56px] font-light tracking-[-0.04em] text-[#1b0624] leading-none">
                    {displayValue}
                </span>
                <span className="text-[20px] text-[#1b0624]/40 font-light">
                    m
                </span>
            </div>

            <p className="text-[14px] text-[#1b0624]/60 font-light leading-relaxed">
                Depth intercept where oceanic temperature reaches exactly 26°C.
            </p>
        </div>
    )
}
export default D26Card