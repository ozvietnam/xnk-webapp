'use client'

import { useState, useEffect } from 'react'

export default function QuyDinhPage() {
  const [regulations, setRegulations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [category, setCategory] = useState('')

  useEffect(() => {
    const url = new URL(`${process.env.NEXT_PUBLIC_API_URL}/api/regulations`)
    if (category) url.searchParams.set('category', category)
    fetch(url.toString())
      .then(r => r.json())
      .then(setRegulations)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [category])

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Quy định Xuất Nhập Khẩu</h1>
      {loading ? (
        <p>Đang tải...</p>
      ) : (
        <div className="space-y-4">
          {regulations.map((reg: any) => (
            <div key={reg.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
              <h2 className="font-semibold text-lg">{reg.title}</h2>
              {reg.category && (
                <span className="text-sm text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                  {reg.category}
                </span>
              )}
              {reg.effective_date && (
                <p className="text-sm text-gray-500 mt-1">
                  Hiệu lực: {reg.effective_date}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
