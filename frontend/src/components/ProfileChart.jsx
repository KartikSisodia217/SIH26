import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
function ProfileChart({ location, profileData }) {
    const data = profileData?.depths?.map((depth, index) => ({
        depth,
        temperature: profileData?.temperatures?.[index] ?? null,
    })) ?? []

    const targetDepths = [0, 50, 100, 150, 200, 300, 500, 700, 1000]
    const tableData = data.filter(d => targetDepths.includes(d.depth))

    return (
        <div className="rounded-[24px] border border-black/5 bg-white shadow-[0_4px_24px_rgba(0,0,0,0.03)] p-8 flex flex-col">
            <div className="flex justify-between items-end mb-6">
                <h3 className="text-[11px] uppercase tracking-widest text-[#1b0624]/40 font-medium">
                    Vertical Profile
                </h3>
                {location && (
                    <p className="text-[13px] font-mono text-[#1b0624]/40">
                        {location.latitude.toFixed(2)}°, {location.longitude.toFixed(2)}°
                    </p>
                )}
            </div>

            {data.length === 0 ? (
                <div className="flex-1 min-h-[300px] flex flex-col items-center justify-center border border-dashed border-black/10 rounded-xl bg-black/[0.02]">
                    <div className="w-10 h-10 mb-4 opacity-20">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                        </svg>
                    </div>
                    <p className="text-[12px] text-[#1b0624]/40 uppercase tracking-widest font-medium text-center px-4">
                        No telemetry data available for this coordinate
                    </p>
                </div>
            ) : (
                <>
                    <div className="h-48 mb-8">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" horizontal={true} vertical={false} />
                                
                                <XAxis
                                    type="number"
                                    dataKey="depth"
                                    stroke="rgba(0,0,0,0.1)"
                                    tick={{ fill: 'rgba(27,6,36,0.4)', fontSize: 11, fontFamily: 'monospace' }}
                                    tickLine={false}
                                    axisLine={false}
                                />

                                <YAxis
                                    type="number"
                                    dataKey="temperature"
                                    stroke="rgba(0,0,0,0.1)"
                                    tick={{ fill: 'rgba(27,6,36,0.4)', fontSize: 11, fontFamily: 'monospace' }}
                                    tickLine={false}
                                    axisLine={false}
                                    domain={['dataMin - 1', 'dataMax + 1']}
                                />

                                <Tooltip 
                                    contentStyle={{ backgroundColor: '#fff', border: '1px solid rgba(0,0,0,0.05)', borderRadius: '12px', fontSize: '12px', boxShadow: '0 4px 24px rgba(0,0,0,0.06)' }}
                                    itemStyle={{ color: '#1b0624' }}
                                    formatter={(value, name) => [value + '°C', name === 'temperature' ? 'Temperature' : name]}
                                    labelFormatter={(label) => 'Depth: ' + label + 'm'}
                                />

                                <Line
                                    type="monotone"
                                    dataKey="temperature"
                                    stroke="#1b0624"
                                    strokeWidth={2}
                                    dot={false}
                                    activeDot={{ r: 4, fill: '#1b0624', stroke: '#fff', strokeWidth: 2 }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    <div>
                        <h4 className="text-[11px] uppercase tracking-widest text-[#1b0624]/40 font-medium mb-3">
                            Temperature by Depth
                        </h4>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-4 gap-y-2">
                            {tableData.map((row) => (
                                <div key={row.depth} className="flex justify-between items-center text-[12px] font-mono border-b border-black/5 py-1">
                                    <span className="text-[#1b0624]/50">{row.depth}m</span>
                                    <span className="text-[#1b0624] font-medium">
                                        {typeof row.temperature === 'number' ? `${row.temperature.toFixed(1)}°C` : 'N/A'}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}
export default ProfileChart