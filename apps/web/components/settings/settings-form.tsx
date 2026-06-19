"use client"

import { useState } from "react"
import { type ThemeConfig } from "@/lib/tenant"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const FONT_OPTIONS = [
  { value: "", label: "Default (Inter)" },
  { value: "Merriweather", label: "Merriweather — elegant serif" },
  { value: "Playfair Display", label: "Playfair Display — classic serif" },
  { value: "Montserrat", label: "Montserrat — modern sans" },
  { value: "Roboto", label: "Roboto — clean sans" },
  { value: "Lato", label: "Lato — friendly sans" },
]

export function SettingsForm({ initialTheme }: { initialTheme: ThemeConfig }) {
  const [inspectorName, setInspectorName] = useState(initialTheme.inspector_name ?? "")
  const [licenseNumber, setLicenseNumber] = useState(initialTheme.license_number ?? "")
  const [email, setEmail] = useState(initialTheme.email ?? "")
  const [moldLicense, setMoldLicense] = useState(initialTheme.mold_license ?? "")
  const [nachiLicense, setNachiLicense] = useState(initialTheme.nachi_license ?? "")
  const [phone, setPhone] = useState(initialTheme.phone ?? "")
  const [website, setWebsite] = useState(initialTheme.website ?? "")
  const [brandName, setBrandName] = useState(initialTheme.brand_name ?? "")
  const [logoUrl, setLogoUrl] = useState(initialTheme.logo_url ?? "")
  const [primaryColor, setPrimaryColor] = useState(initialTheme.primary_color ?? "#2563eb")
  const [fontFamily, setFontFamily] = useState(initialTheme.font_family ?? "")
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">("idle")
  const [errorMsg, setErrorMsg] = useState("")

  async function handleSave() {
    setStatus("saving")
    setErrorMsg("")
    try {
      const res = await fetch("/api/tenants/me/theme", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          theme_config: {
            inspector_name: inspectorName || null,
            license_number: licenseNumber || null,
            email: email || null,
            mold_license: moldLicense || null,
            nachi_license: nachiLicense || null,
            phone: phone || null,
            website: website || null,
            brand_name: brandName || null,
            logo_url: logoUrl || null,
            primary_color: primaryColor || null,
            font_family: fontFamily || null,
          },
        }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => null)
        throw new Error(
          (data?.detail as string | undefined) ??
            (data?.error as string | undefined) ??
            "Failed to save settings.",
        )
      }
      setStatus("saved")
      setTimeout(() => setStatus("idle"), 3000)
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to save settings.")
      setStatus("error")
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Inspector Info */}
      <div className="rounded-lg border border-border bg-card p-6">
        <h2 className="mb-4 text-base font-medium text-foreground">Inspector Info</h2>
        <div className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="inspector-name">Inspector Name</Label>
            <Input
              id="inspector-name"
              type="text"
              value={inspectorName}
              onChange={(e) => setInspectorName(e.target.value)}
              placeholder="Marcus Reyes"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="license-number">License Number</Label>
            <Input
              id="license-number"
              type="text"
              value={licenseNumber}
              onChange={(e) => setLicenseNumber(e.target.value)}
              placeholder="HI-XXXXX"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="inspector@email.com"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="mold-license">Mold Inspector License</Label>
            <Input
              id="mold-license"
              type="text"
              value={moldLicense}
              onChange={(e) => setMoldLicense(e.target.value)}
              placeholder="MRSA-XXXX"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="nachi-license">NACHI License</Label>
            <Input
              id="nachi-license"
              type="text"
              value={nachiLicense}
              onChange={(e) => setNachiLicense(e.target.value)}
              placeholder="0511XXXX"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="phone">Phone</Label>
            <Input
              id="phone"
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="(305) 555-0142"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="website">Website</Label>
            <Input
              id="website"
              type="url"
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              placeholder="https://yoursite.com"
            />
          </div>
        </div>
      </div>

      {/* Branding */}
      <div className="rounded-lg border border-border bg-card p-6">
        <h2 className="mb-4 text-base font-medium text-foreground">Branding</h2>
        <div className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="brand-name">Brand Name</Label>
            <Input
              id="brand-name"
              type="text"
              value={brandName}
              onChange={(e) => setBrandName(e.target.value)}
              placeholder="Your company name"
            />
            <p className="text-xs text-muted-foreground">
              Shown in the portal header and on reports.
            </p>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="logo-url">Logo URL</Label>
            <Input
              id="logo-url"
              type="url"
              value={logoUrl}
              onChange={(e) => setLogoUrl(e.target.value)}
              placeholder="https://example.com/logo.png"
            />
            <p className="text-xs text-muted-foreground">
              Enter a direct image URL (ends in .png, .jpg, .svg, etc.). Google Drive share links
              don&apos;t work — use a direct hosting service like Imgur, Cloudinary, or your own server.
            </p>
            {logoUrl && (
              <div className="mt-2 flex min-h-12 items-center justify-center rounded-md border border-border bg-muted/40 p-3">
                <img
                  src={logoUrl}
                  alt="Logo preview"
                  className="max-h-16 max-w-48 object-contain"
                />
              </div>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="primary-color-text">Primary Color</Label>
            <div className="flex items-center gap-2">
              <input
                id="primary-color-picker"
                type="color"
                value={primaryColor}
                onChange={(e) => setPrimaryColor(e.target.value)}
                className="h-8 w-10 cursor-pointer rounded border border-input bg-transparent p-0.5"
                aria-label="Pick primary color"
              />
              <Input
                id="primary-color-text"
                type="text"
                value={primaryColor}
                onChange={(e) => setPrimaryColor(e.target.value)}
                placeholder="#2563eb"
                className="w-32 font-mono"
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Stored for future use on reports. CSS application coming soon.
            </p>
          </div>
        </div>
      </div>

      {/* Report Typography */}
      <div className="rounded-lg border border-border bg-card p-6">
        <h2 className="mb-4 text-base font-medium text-foreground">Report Typography</h2>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="font-family">Font Family</Label>
          <Select value={fontFamily} onValueChange={(v) => setFontFamily(v ?? "")}>
            <SelectTrigger id="font-family" className="w-full">
              <SelectValue placeholder="Default (Inter)" />
            </SelectTrigger>
            <SelectContent>
              {FONT_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            Used in generated PDF reports only.
          </p>
        </div>
      </div>

      {/* Save */}
      <div className="flex items-center gap-3">
        <Button onClick={handleSave} disabled={status === "saving"}>
          {status === "saving" ? "Saving…" : "Save"}
        </Button>
        {status === "saved" && (
          <span className="text-sm text-green-600 dark:text-green-400">Saved ✓</span>
        )}
        {status === "error" && (
          <span className="text-sm text-destructive">{errorMsg}</span>
        )}
      </div>
    </div>
  )
}
