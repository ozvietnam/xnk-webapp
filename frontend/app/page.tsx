import Link from 'next/link'

export default function HomePage() {
  return (
    <div className="container mx-auto px-4 py-16">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-primary mb-4">
          Tra cứu HS Code & Thuế XNK
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Tìm kiếm nhanh mã HS, thuế suất, quy định XNK Việt Nam – Trung Quốc
        </p>
        <div className="flex gap-4 justify-center flex-wrap">
          <Link href="/tra-cuu-hs" className="btn-primary">
            Tra cứu HS Code
          </Link>
          <Link href="/chatbot" className="btn-secondary">
            Chatbot AI
          </Link>
          <Link href="/quy-dinh" className="btn-outline">
            Quy định XNK
          </Link>
        </div>
      </div>
    </div>
  )
}
