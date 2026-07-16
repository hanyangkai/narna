import { useEffect, useState } from "react";
import QRCode from "qrcode";

type Props = {
  payload: string;
  label?: string;
  size?: number;
};

export default function PaymentQr({ payload, label = "Scan to pay", size = 200 }: Props) {
  const [dataUrl, setDataUrl] = useState<string | null>(null);

  useEffect(() => {
    QRCode.toDataURL(payload, {
      width: size,
      margin: 2,
      color: { dark: "#0f172a", light: "#ffffff" },
    })
      .then(setDataUrl)
      .catch(() => setDataUrl(null));
  }, [payload, size]);

  if (!dataUrl) return null;

  return (
    <div className="payment-qr">
      <p className="payment-qr-label">{label}</p>
      <img src={dataUrl} alt="Payment QR code" width={size} height={size} />
    </div>
  );
}
