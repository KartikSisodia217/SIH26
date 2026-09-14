import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
function ProfileChart({ location, profileData }) {
    const data = profileData?.depths?.map((depth, index) => ({
        depth,
        temperature: profileData.temperatures[index],
    })) ?? []

    return (
        <div className="rounded-[24px] border border-black/5 bg-white shadow-[0_4px_24px_rgba(0,0,0,0.03)] p-8">
            <div className="flex justify-between items-end mb-8">
                <h3 className="text-[11px] uppercase tracking-widest text-[#1b0624]/40 font-medium">
                    Vertical Profile
                </h3>
                {location && (
                    <p className="text-[13px] font-mono text-[#1b0624]/40">
                        {location.latitude.toFixed(2)}°, {location.longitude.toFixed(2)}°
                    </p>
                )}
            </div>

            <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data} layout="vertical" margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" horizontal={true} vertical={false} />
                        
                        <XAxis
                            type="number"
                            dataKey="temperature"
                            stroke="rgba(0,0,0,0.1)"
                            tick={{ fill: 'rgba(27,6,36,0.4)', fontSize: 11, fontFamily: 'monospace' }}
                            tickLine={false}
                            axisLine={false}
                            domain={['dataMin - 1', 'dataMax + 1']}
                            orientation="top"
                        />

                        <YAxis
                            type="number"
                            dataKey="depth"
                            stroke="rgba(0,0,0,0.1)"
                            tick={{ fill: 'rgba(27,6,36,0.4)', fontSize: 11, fontFamily: 'monospace' }}
                            tickLine={false}
                            axisLine={false}
                            reversed={true}
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
        </div>
    )
}
export default ProfileChart