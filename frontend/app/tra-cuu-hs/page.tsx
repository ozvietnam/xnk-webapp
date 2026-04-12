'use client'

import { useState } from 'react'

export default function TraCuuHSPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/hs-codes/search?q=${encodeURIComponent(query)}&limit=20`
      )
      const data = await res.json()
      setResults(data.results || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Tra cứu mã HS</h1>

      <form onSubmit={handleSearch} className="flex gap-2 mb-8">
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Nhập tên hàng hoá hoặc mã HS..."
          className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-primary text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Đang tìm...' : 'Tìm kiếm'}
        </button>
      </form>

      {results.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="border px-4 py-2 text-left">Mã HS</th>
                <th className="border px-4 py-2 text-left">Mô tả</th>
                <th className="border px-4 py-2 text-right">Thuế MFN (%)</th>
                <th className="border px-4 py-2 text-right">Thuế ưu đãi (%)</th>
                <th className="border px-4 py-2 text-left">Đơn vị</th>
              </tr>
            </thead>
            <tbody>
              {results.map((item: any) => (
                <tr key={item.code} className="hover:bg-gray-50">
                  <td className="border px-4 py-2 font-mono font-semibold">{item.code}</td>
                  <td className="border px-4 py-2">{item.description_vi}</td>
                  <td className="border px-4 py-2 text-right">{item.tax_rate_normal ?? '—'}</td>
                  <td className="border px-4 py-2 text-right">{item.tax_rate_preferential ?? '—'}</td>
                  <td className="border px-4 py-2">{item.unit ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
