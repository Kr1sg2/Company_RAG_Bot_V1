import { useEffect, useState } from "react";
import { getAdminBranding, putAdminBranding, type Branding } from "../lib/api";

export default function AdminBranding() {
  const [auth] = useState(() => localStorage.getItem("auth") || "");
  const [data, setData] = useState<Branding | null>(null);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [ok, setOk] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const s = await getAdminBranding(auth);
        setData(s);
      } catch (e: any) {
        setErr(`Load failed: ${e?.message ?? "error"}`);
      }
    })();
  }, [auth]);

  async function save() {
    if (!data) return;
    setSaving(true); setErr(null); setOk(false);
    try {
      const res = await putAdminBranding(auth, data);
      setData(res);
      setOk(true);
    } catch (e: any) {
      setErr(`Save failed: ${e?.message ?? "error"}`);
    } finally {
      setSaving(false);
    }
  }

  if (!data) return <div className="min-h-screen grid place-items-center">Loading… {err}</div>;

  return (
    <div className="min-h-screen p-6 bg-zinc-100">
      <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow p-6 space-y-6">
        <header className="flex items-center justify-between">
          <h1 className="text-xl font-semibold">Branding Settings</h1>
          <div className="flex gap-2">
            <button onClick={save} disabled={saving} className="rounded-lg bg-black text-white px-4 py-2 disabled:opacity-50">
              {saving ? "Saving…" : "Save"}
            </button>
          </div>
        </header>

        {err && <div className="text-red-600 text-sm bg-red-50 p-3 rounded-lg">{err}</div>}
        {ok && <div className="text-green-600 text-sm bg-green-50 p-3 rounded-lg">Saved ✅</div>}

        {/* Basic Settings */}
        <section className="bg-gray-50 rounded-lg p-4 space-y-4">
          <h2 className="text-lg font-medium">Basic Settings</h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <label className="block">
              <span className="text-sm font-medium">Company Name</span>
              <input 
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.companyName}
                onChange={e => setData({ ...data, companyName: e.target.value })} 
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Tagline Text</span>
              <input 
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.taglineText ?? ""}
                onChange={e => setData({ ...data, taglineText: e.target.value })} 
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Empty State Text</span>
              <input 
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.emptyStateText ?? ""}
                onChange={e => setData({ ...data, emptyStateText: e.target.value })} 
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Input Placeholder</span>
              <input 
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.inputPlaceholder ?? ""}
                onChange={e => setData({ ...data, inputPlaceholder: e.target.value })} 
              />
            </label>
          </div>
        </section>

        {/* Fonts - Typography Controls */}
        <section className="bg-gray-50 rounded-lg p-4 space-y-4">
          <h2 className="text-lg font-medium">Fonts & Typography</h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <label className="block">
              <span className="text-sm font-medium">Font Family</span>
              <select 
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.fontFamily ?? "system-ui"}
                onChange={e => setData({ ...data, fontFamily: e.target.value })} 
              >
                <option value="system-ui">System UI</option>
                <option value="Inter, sans-serif">Inter</option>
                <option value="Roboto, sans-serif">Roboto</option>
                <option value="Open Sans, sans-serif">Open Sans</option>
                <option value="Poppins, sans-serif">Poppins</option>
                <option value="Arial, sans-serif">Arial</option>
                <option value="Georgia, serif">Georgia</option>
                <option value="Times New Roman, serif">Times</option>
                <option value="Courier New, monospace">Courier</option>
              </select>
            </label>

            <label className="block">
              <span className="text-sm font-medium">Title Font Size (px)</span>
              <input 
                type="number"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.titleFontSize ?? 32}
                onChange={e => setData({ ...data, titleFontSize: parseInt(e.target.value) })} 
                min="12" max="72"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Body Font Size (px)</span>
              <input 
                type="number"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.bodyFontSize ?? 16}
                onChange={e => setData({ ...data, bodyFontSize: parseInt(e.target.value) })} 
                min="10" max="32"
              />
            </label>

            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <input 
                  type="checkbox"
                  className="mr-2"
                  checked={data.titleBold ?? true}
                  onChange={e => setData({ ...data, titleBold: e.target.checked })} 
                />
                <span className="text-sm font-medium">Bold Title</span>
              </label>

              <label className="flex items-center">
                <input 
                  type="checkbox"
                  className="mr-2"
                  checked={data.titleItalic ?? false}
                  onChange={e => setData({ ...data, titleItalic: e.target.checked })} 
                />
                <span className="text-sm font-medium">Italic Title</span>
              </label>
            </div>

            <label className="block">
              <span className="text-sm font-medium">Tagline Font Size (px)</span>
              <input 
                type="number"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.taglineFontSize ?? 18}
                onChange={e => setData({ ...data, taglineFontSize: parseInt(e.target.value) })} 
                min="10" max="24"
              />
            </label>

            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <input 
                  type="checkbox"
                  className="mr-2"
                  checked={data.taglineBold ?? false}
                  onChange={e => setData({ ...data, taglineBold: e.target.checked })} 
                />
                <span className="text-sm font-medium">Bold Tagline</span>
              </label>

              <label className="flex items-center">
                <input 
                  type="checkbox"
                  className="mr-2"
                  checked={data.taglineItalic ?? false}
                  onChange={e => setData({ ...data, taglineItalic: e.target.checked })} 
                />
                <span className="text-sm font-medium">Italic Tagline</span>
              </label>
            </div>
          </div>
        </section>

        {/* Colors */}
        <section className="bg-gray-50 rounded-lg p-4 space-y-4">
          <h2 className="text-lg font-medium">Colors</h2>
          
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <label className="block">
              <span className="text-sm font-medium">Primary Color</span>
              <input 
                type="color"
                className="w-full h-10 border rounded-lg mt-1"
                value={data.colors.primary}
                onChange={e => setData({ ...data, colors: { ...data.colors, primary: e.target.value } })} 
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Accent Color</span>
              <input 
                type="color"
                className="w-full h-10 border rounded-lg mt-1"
                value={data.colors.accent}
                onChange={e => setData({ ...data, colors: { ...data.colors, accent: e.target.value } })} 
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Background Color</span>
              <input 
                type="color"
                className="w-full h-10 border rounded-lg mt-1"
                value={data.colors.bg}
                onChange={e => setData({ ...data, colors: { ...data.colors, bg: e.target.value } })} 
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Text Color</span>
              <input 
                type="color"
                className="w-full h-10 border rounded-lg mt-1"
                value={data.colors.text}
                onChange={e => setData({ ...data, colors: { ...data.colors, text: e.target.value } })} 
              />
            </label>
          </div>
        </section>

        {/* Chat Bubbles */}
        <section className="bg-gray-50 rounded-lg p-4 space-y-4">
          <h2 className="text-lg font-medium">Chat Bubbles</h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <label className="block">
              <span className="text-sm font-medium">Border Radius (px)</span>
              <input 
                type="number"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={parseInt(data.bubbles.radius) || 12}
                onChange={e => setData({ ...data, bubbles: { ...data.bubbles, radius: `${e.target.value}px` } })} 
                min="0" max="32"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Bubble Padding (px)</span>
              <input 
                type="number"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.bubblePadding ?? 12}
                onChange={e => setData({ ...data, bubblePadding: parseInt(e.target.value) })} 
                min="6" max="24"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Max Bubble Width (%)</span>
              <input 
                type="number"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.bubbleMaxWidth ?? 70}
                onChange={e => setData({ ...data, bubbleMaxWidth: parseInt(e.target.value) })} 
                min="40" max="90"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">AI Bubble Background</span>
              <input 
                type="color"
                className="w-full h-10 border rounded-lg mt-1"
                value={data.bubbles.aiBg}
                onChange={e => setData({ ...data, bubbles: { ...data.bubbles, aiBg: e.target.value } })} 
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">AI Bubble Text Color</span>
              <input 
                type="color"
                className="w-full h-10 border rounded-lg mt-1"
                value={data.aiTextColor ?? "#000000"}
                onChange={e => setData({ ...data, aiTextColor: e.target.value })} 
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">AI Bubble Border</span>
              <input 
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.aiBubbleBorder ?? "none"}
                onChange={e => setData({ ...data, aiBubbleBorder: e.target.value })} 
                placeholder="1px solid #ddd or none"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">User Bubble Background</span>
              <input 
                type="color"
                className="w-full h-10 border rounded-lg mt-1"
                value={data.bubbles.userBg}
                onChange={e => setData({ ...data, bubbles: { ...data.bubbles, userBg: e.target.value } })} 
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">User Bubble Text Color</span>
              <input 
                type="color"
                className="w-full h-10 border rounded-lg mt-1"
                value={data.userTextColor ?? "#ffffff"}
                onChange={e => setData({ ...data, userTextColor: e.target.value })} 
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">User Bubble Border</span>
              <input 
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.userBubbleBorder ?? "none"}
                onChange={e => setData({ ...data, userBubbleBorder: e.target.value })} 
                placeholder="1px solid #ddd or none"
              />
            </label>
          </div>
        </section>

        {/* Chat Card Dimensions */}
        <section className="bg-gray-50 rounded-lg p-4 space-y-4">
          <h2 className="text-lg font-medium">Chat Card Sizing</h2>
          
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <label className="block">
              <span className="text-sm font-medium">Chat Width (px)</span>
              <input 
                type="number"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.chatWidth}
                onChange={e => setData({ ...data, chatWidth: e.target.value })} 
                min="300" max="1200"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Chat Height (vh)</span>
              <input 
                type="number"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.chatHeight}
                onChange={e => setData({ ...data, chatHeight: e.target.value })} 
                min="40" max="90"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Card Radius (px)</span>
              <input 
                type="number"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.cardRadius}
                onChange={e => setData({ ...data, cardRadius: e.target.value })} 
                min="0" max="32"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Card Padding (px)</span>
              <input 
                type="number"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.cardPadding ?? 24}
                onChange={e => setData({ ...data, cardPadding: parseInt(e.target.value) })} 
                min="8" max="48"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Input Box Height (px)</span>
              <input 
                type="number"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.inputHeight ?? 44}
                onChange={e => setData({ ...data, inputHeight: parseInt(e.target.value) })} 
                min="32" max="64"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Input Box Radius (px)</span>
              <input 
                type="number"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.inputRadius ?? 8}
                onChange={e => setData({ ...data, inputRadius: parseInt(e.target.value) })} 
                min="0" max="24"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Message Spacing (px)</span>
              <input 
                type="number"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.messageSpacing ?? 16}
                onChange={e => setData({ ...data, messageSpacing: parseInt(e.target.value) })} 
                min="4" max="32"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Vertical Margin (px)</span>
              <input 
                type="number"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.chatOffsetTop}
                onChange={e => setData({ ...data, chatOffsetTop: e.target.value })} 
                min="0" max="100"
              />
            </label>
          </div>
        </section>

        {/* Images */}
        <section className="bg-gray-50 rounded-lg p-4 space-y-4">
          <h2 className="text-lg font-medium">Images & Assets</h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <label className="block">
              <span className="text-sm font-medium">Logo URL</span>
              <input 
                type="url"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.logoDataUrl ?? ""}
                onChange={e => setData({ ...data, logoDataUrl: e.target.value })} 
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Page Background URL</span>
              <input 
                type="url"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.pageBackgroundUrl ?? ""}
                onChange={e => setData({ ...data, pageBackgroundUrl: e.target.value })} 
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Chat Card Background URL</span>
              <input 
                type="url"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.chatCardBackgroundUrl ?? ""}
                onChange={e => setData({ ...data, chatCardBackgroundUrl: e.target.value })} 
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Favicon URL</span>
              <input 
                type="url"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.faviconUrl ?? ""}
                onChange={e => setData({ ...data, faviconUrl: e.target.value })} 
              />
            </label>
          </div>
        </section>

        {/* Backgrounds & Shadows */}
        <section className="bg-gray-50 rounded-lg p-4 space-y-4">
          <h2 className="text-lg font-medium">Backgrounds & Shadows</h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <label className="block">
              <span className="text-sm font-medium">Page Background Color</span>
              <input 
                type="color"
                className="w-full h-10 border rounded-lg mt-1"
                value={data.pageBackgroundColor ?? "#ffffff"}
                onChange={e => setData({ ...data, pageBackgroundColor: e.target.value })} 
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Page Background Image URL</span>
              <input 
                type="url"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.pageBackgroundUrl ?? ""}
                onChange={e => setData({ ...data, pageBackgroundUrl: e.target.value || null })} 
                placeholder="https://example.com/background.jpg"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Card Background Color</span>
              <input 
                type="color"
                className="w-full h-10 border rounded-lg mt-1"
                value={data.cardBackgroundColor ?? "#ffffff"}
                onChange={e => setData({ ...data, cardBackgroundColor: e.target.value })} 
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Card Background Image URL</span>
              <input 
                type="url"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.chatCardBackgroundUrl ?? ""}
                onChange={e => setData({ ...data, chatCardBackgroundUrl: e.target.value || null })} 
                placeholder="https://example.com/card-bg.jpg"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Card Background (CSS Override)</span>
              <input 
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.cardBg}
                onChange={e => setData({ ...data, cardBg: e.target.value })} 
                placeholder="rgba(255,255,255,0.88) or linear-gradient(...)"
              />
              <div className="text-xs text-gray-500 mt-1">
                Advanced: Overrides color/image above. Use CSS values like rgba(), gradients, etc.
              </div>
            </label>

            <label className="block">
              <span className="text-sm font-medium">Card Transparency (%)</span>
              <input 
                type="range"
                min="0" max="100"
                className="w-full mt-1"
                value={data.cardOpacity ?? 100}
                onChange={e => setData({ ...data, cardOpacity: parseInt(e.target.value) })} 
              />
              <div className="text-xs text-gray-500 mt-1">
                Current: {data.cardOpacity ?? 100}% opacity
              </div>
            </label>
          </div>

          <div className="border-t pt-4 mt-4">
            <h3 className="text-md font-medium mb-3">Card Shadow/Glow Effects</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <label className="block">
                <span className="text-sm font-medium">Shadow Color</span>
                <input 
                  type="color"
                  className="w-full h-10 border rounded-lg mt-1"
                  value={data.shadowColor ?? "#000000"}
                  onChange={e => setData({ ...data, shadowColor: e.target.value })} 
                />
              </label>

              <label className="block">
                <span className="text-sm font-medium">Shadow Blur (px)</span>
                <input 
                  type="range"
                  min="0" max="50"
                  className="w-full mt-1"
                  value={data.shadowBlur ?? 10}
                  onChange={e => setData({ ...data, shadowBlur: parseInt(e.target.value) })} 
                />
                <div className="text-xs text-gray-500 mt-1">
                  {data.shadowBlur ?? 10}px
                </div>
              </label>

              <label className="block">
                <span className="text-sm font-medium">Shadow Spread (px)</span>
                <input 
                  type="range"
                  min="0" max="20"
                  className="w-full mt-1"
                  value={data.shadowSpread ?? 0}
                  onChange={e => setData({ ...data, shadowSpread: parseInt(e.target.value) })} 
                />
                <div className="text-xs text-gray-500 mt-1">
                  {data.shadowSpread ?? 0}px
                </div>
              </label>

              <label className="block">
                <span className="text-sm font-medium">Shadow Opacity (%)</span>
                <input 
                  type="range"
                  min="0" max="100"
                  className="w-full mt-1"
                  value={data.shadowOpacity ?? 20}
                  onChange={e => setData({ ...data, shadowOpacity: parseInt(e.target.value) })} 
                />
                <div className="text-xs text-gray-500 mt-1">
                  {data.shadowOpacity ?? 20}%
                </div>
              </label>

              <label className="flex items-center col-span-2">
                <input 
                  type="checkbox"
                  className="mr-2"
                  checked={data.enableShadow ?? true}
                  onChange={e => setData({ ...data, enableShadow: e.target.checked })} 
                />
                <span className="text-sm font-medium">Enable Card Shadow</span>
              </label>

              <label className="flex items-center col-span-2">
                <input 
                  type="checkbox"
                  className="mr-2"
                  checked={data.enableGlow ?? false}
                  onChange={e => setData({ ...data, enableGlow: e.target.checked })} 
                />
                <span className="text-sm font-medium">Enable Glow Effect</span>
              </label>
            </div>
          </div>
        </section>

        {/* Robot / Avatar */}
        <section className="bg-gray-50 rounded-lg p-4 space-y-4">
          <h2 className="text-lg font-medium">Robot / Avatar</h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <label className="block">
              <span className="text-sm font-medium">Avatar Image URL</span>
              <input 
                type="url"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.avatarImageUrl ?? ""}
                onChange={e => setData({ ...data, avatarImageUrl: e.target.value || null })} 
                placeholder="https://example.com/robot-avatar.png"
              />
              <div className="text-xs text-gray-500 mt-1">
                Robot/AI assistant avatar displayed in chat. Leave empty to hide.
              </div>
            </label>

            <label className="block">
              <span className="text-sm font-medium">Avatar Size (px)</span>
              <input 
                type="number"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.avatarSize ?? 40}
                onChange={e => setData({ ...data, avatarSize: parseInt(e.target.value) })} 
                min="24" max="80"
              />
              <div className="text-xs text-gray-500 mt-1">
                Size of the avatar image in pixels
              </div>
            </label>

            <label className="block">
              <span className="text-sm font-medium">Avatar Position</span>
              <select 
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.avatarPosition ?? "left"}
                onChange={e => setData({ ...data, avatarPosition: e.target.value })} 
              >
                <option value="left">Left of AI messages</option>
                <option value="right">Right of AI messages</option>
                <option value="none">Hide avatar</option>
              </select>
            </label>

            <label className="block">
              <span className="text-sm font-medium">Avatar Shape</span>
              <select 
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.avatarShape ?? "circle"}
                onChange={e => setData({ ...data, avatarShape: e.target.value })} 
              >
                <option value="circle">Circle</option>
                <option value="square">Square</option>
                <option value="rounded">Rounded Square</option>
              </select>
            </label>

            <label className="flex items-center col-span-2">
              <input 
                type="checkbox"
                className="mr-2"
                checked={data.showAvatarOnMobile ?? true}
                onChange={e => setData({ ...data, showAvatarOnMobile: e.target.checked })} 
              />
              <span className="text-sm font-medium">Show avatar on mobile devices</span>
            </label>
          </div>
        </section>

        {/* Audio / TTS & STT */}
        <section className="bg-gray-50 rounded-lg p-4 space-y-4">
          <h2 className="text-lg font-medium">Audio / Speech Controls</h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <label className="flex items-center">
              <input 
                type="checkbox"
                className="mr-3"
                checked={data.enableTextToSpeech ?? false}
                onChange={e => setData({ ...data, enableTextToSpeech: e.target.checked })} 
              />
              <div>
                <span className="text-sm font-medium">Enable Text-to-Speech</span>
                <div className="text-xs text-gray-500 mt-1">
                  Allow AI responses to be read aloud
                </div>
              </div>
            </label>

            <label className="flex items-center">
              <input 
                type="checkbox"
                className="mr-3"
                checked={data.enableSpeechToText ?? false}
                onChange={e => setData({ ...data, enableSpeechToText: e.target.checked })} 
              />
              <div>
                <span className="text-sm font-medium">Enable Speech-to-Text</span>
                <div className="text-xs text-gray-500 mt-1">
                  Allow users to speak their messages
                </div>
              </div>
            </label>

            <label className="block">
              <span className="text-sm font-medium">TTS Voice Selection</span>
              <select 
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.ttsVoice ?? "default"}
                onChange={e => setData({ ...data, ttsVoice: e.target.value })} 
                disabled={!data.enableTextToSpeech}
              >
                <option value="default">Default System Voice</option>
                <option value="male">Male Voice</option>
                <option value="female">Female Voice</option>
                <option value="neural">Neural Voice</option>
              </select>
            </label>

            <label className="block">
              <span className="text-sm font-medium">TTS Speed</span>
              <input 
                type="range"
                min="0.5" max="2" step="0.1"
                className="w-full mt-1"
                value={data.ttsSpeed ?? 1.0}
                onChange={e => setData({ ...data, ttsSpeed: parseFloat(e.target.value) })} 
                disabled={!data.enableTextToSpeech}
              />
              <div className="text-xs text-gray-500 mt-1">
                Speed: {data.ttsSpeed ?? 1.0}x
              </div>
            </label>

            <label className="block">
              <span className="text-sm font-medium">STT Language</span>
              <select 
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.sttLanguage ?? "en-US"}
                onChange={e => setData({ ...data, sttLanguage: e.target.value })} 
                disabled={!data.enableSpeechToText}
              >
                <option value="en-US">English (US)</option>
                <option value="en-GB">English (UK)</option>
                <option value="es-ES">Spanish</option>
                <option value="fr-FR">French</option>
                <option value="de-DE">German</option>
                <option value="it-IT">Italian</option>
                <option value="pt-PT">Portuguese</option>
                <option value="ja-JP">Japanese</option>
                <option value="zh-CN">Chinese (Simplified)</option>
              </select>
            </label>

            <label className="flex items-center">
              <input 
                type="checkbox"
                className="mr-3"
                checked={data.sttAutoSend ?? false}
                onChange={e => setData({ ...data, sttAutoSend: e.target.checked })} 
                disabled={!data.enableSpeechToText}
              />
              <div>
                <span className="text-sm font-medium">Auto-send after speech</span>
                <div className="text-xs text-gray-500 mt-1">
                  Automatically send message after speech recognition
                </div>
              </div>
            </label>

            <label className="flex items-center">
              <input 
                type="checkbox"
                className="mr-3"
                checked={data.showAudioControls ?? true}
                onChange={e => setData({ ...data, showAudioControls: e.target.checked })} 
              />
              <div>
                <span className="text-sm font-medium">Show audio control buttons</span>
                <div className="text-xs text-gray-500 mt-1">
                  Display microphone and speaker buttons in chat interface
                </div>
              </div>
            </label>

            <label className="flex items-center">
              <input 
                type="checkbox"
                className="mr-3"
                checked={data.ttsAutoPlay ?? false}
                onChange={e => setData({ ...data, ttsAutoPlay: e.target.checked })} 
                disabled={!data.enableTextToSpeech}
              />
              <div>
                <span className="text-sm font-medium">Auto-play AI responses</span>
                <div className="text-xs text-gray-500 mt-1">
                  Automatically speak AI responses without clicking play
                </div>
              </div>
            </label>
          </div>
        </section>

        {/* LLM Controls */}
        <section className="bg-gray-50 rounded-lg p-4 space-y-4">
          <h2 className="text-lg font-medium">LLM Settings</h2>
          <div className="text-xs text-gray-500 mb-4">
            These settings control the AI model behavior. Changes apply to new conversations only.
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <label className="block">
              <span className="text-sm font-medium">AI Model</span>
              <select 
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.aiModel ?? "gpt-4"}
                onChange={e => setData({ ...data, aiModel: e.target.value })} 
              >
                <option value="gpt-4">GPT-4 (Recommended)</option>
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                <option value="claude-3">Claude 3</option>
                <option value="claude-3-haiku">Claude 3 Haiku</option>
              </select>
            </label>

            <label className="block">
              <span className="text-sm font-medium">Temperature</span>
              <input 
                type="range"
                min="0" max="2" step="0.1"
                className="w-full mt-1"
                value={data.aiTemperature ?? 0.7}
                onChange={e => setData({ ...data, aiTemperature: parseFloat(e.target.value) })} 
              />
              <div className="text-xs text-gray-500 mt-1">
                {data.aiTemperature ?? 0.7} - Lower = more focused, Higher = more creative
              </div>
            </label>

            <label className="block">
              <span className="text-sm font-medium">Max Response Tokens</span>
              <input 
                type="number"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.aiMaxTokens ?? 2048}
                onChange={e => setData({ ...data, aiMaxTokens: parseInt(e.target.value) })} 
                min="64" max="8000"
              />
              <div className="text-xs text-gray-500 mt-1">
                Maximum length of AI responses (64-8000 tokens)
              </div>
            </label>

            <label className="block">
              <span className="text-sm font-medium">Top K Sampling</span>
              <input 
                type="number"
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.aiTopK ?? 50}
                onChange={e => setData({ ...data, aiTopK: parseInt(e.target.value) })} 
                min="1" max="100"
              />
              <div className="text-xs text-gray-500 mt-1">
                Controls response diversity (1-100, lower = more focused)
              </div>
            </label>

            <label className="block">
              <span className="text-sm font-medium">Response Strictness</span>
              <select 
                className="w-full border rounded-lg px-3 py-2 mt-1"
                value={data.aiStrictness ?? "balanced"}
                onChange={e => setData({ ...data, aiStrictness: e.target.value })} 
              >
                <option value="creative">Creative - More flexible responses</option>
                <option value="balanced">Balanced - Standard behavior</option>
                <option value="precise">Precise - More accurate, less creative</option>
                <option value="strict">Strict - Highly focused responses</option>
              </select>
            </label>

            <label className="block">
              <span className="text-sm font-medium">System Prompt</span>
              <textarea 
                className="w-full border rounded-lg px-3 py-2 mt-1"
                rows={3}
                value={data.aiSystemPrompt ?? "You are a helpful AI assistant."}
                onChange={e => setData({ ...data, aiSystemPrompt: e.target.value })} 
                placeholder="You are a helpful AI assistant that..."
              />
              <div className="text-xs text-gray-500 mt-1">
                Instructions that define the AI's personality and behavior
              </div>
            </label>

            <label className="flex items-center col-span-2">
              <input 
                type="checkbox"
                className="mr-3"
                checked={data.aiStreamResponses ?? true}
                onChange={e => setData({ ...data, aiStreamResponses: e.target.checked })} 
              />
              <div>
                <span className="text-sm font-medium">Stream responses in real-time</span>
                <div className="text-xs text-gray-500 mt-1">
                  Show AI responses as they're being generated (recommended)
                </div>
              </div>
            </label>

            <label className="flex items-center col-span-2">
              <input 
                type="checkbox"
                className="mr-3"
                checked={data.aiRetainContext ?? true}
                onChange={e => setData({ ...data, aiRetainContext: e.target.checked })} 
              />
              <div>
                <span className="text-sm font-medium">Retain conversation context</span>
                <div className="text-xs text-gray-500 mt-1">
                  Allow AI to remember earlier messages in the conversation
                </div>
              </div>
            </label>
          </div>
        </section>

        {/* Live Preview */}
        <section className="bg-gray-50 rounded-lg p-4 space-y-4">
          <h2 className="text-lg font-medium">Live Preview</h2>
          
          <div 
            className="p-6 rounded-xl border"
            style={{
              backgroundColor: data.colors.bg,
              color: data.colors.text,
              maxWidth: `${data.chatWidth}px`,
              margin: '0 auto'
            }}
          >
            <div className="text-center space-y-4">
              <h3 className="text-xl font-bold">{data.companyName}</h3>
              {data.taglineText && (
                <p className="text-sm opacity-80">{data.taglineText}</p>
              )}
              
              <div className="space-y-2 mt-4">
                <div 
                  className="inline-block px-4 py-2 max-w-[70%]"
                  style={{
                    backgroundColor: data.bubbles.aiBg,
                    borderRadius: data.bubbles.radius,
                    color: data.colors.text
                  }}
                >
                  {data.emptyStateText || "Sample AI message"}
                </div>
                
                <div className="text-right">
                  <div 
                    className="inline-block px-4 py-2 max-w-[70%]"
                    style={{
                      backgroundColor: data.bubbles.userBg,
                      borderRadius: data.bubbles.radius,
                      color: data.colors.text
                    }}
                  >
                    Sample user message
                  </div>
                </div>
              </div>

              <div 
                className="p-3 rounded-lg border"
                style={{ backgroundColor: data.cardBg }}
              >
                <input 
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder={data.inputPlaceholder || "Type your message..."}
                  readOnly
                />
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}