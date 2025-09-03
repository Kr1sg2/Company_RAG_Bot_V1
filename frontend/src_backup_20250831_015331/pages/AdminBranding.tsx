import { getAdminBranding, putAdminBranding } from "../lib/api";
import type { Branding } from "../lib/brandingTypes";
import { useEffect, useState, useRef } from 'react';
import { BrandingStyleMapper } from '../lib/brandingToStyles';
import { floatToPct, pctToFloat } from '../lib/color';
// Complete default branding values for every field
const DEFAULTS: Branding = {
  // Basic
  companyName: 'LexaAI Company Assistant',
  taglineText: 'Ask me anything about our company docs',
  emptyStateText: 'Start by asking something like "What is our company policy?"',
  inputPlaceholder: 'Type your question…',
  
  // Typography
  fontFamily: 'Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif',
  titleFontSize: 38,
  bodyFontSize: 16,
  titleBold: true,
  titleItalic: false,
  taglineFontSize: 16,
  taglineBold: false,
  taglineItalic: false,
  
  // Colors
  primaryColor: '#6190ff',
  accentColor: '#756bff',
  textColor: '#121212',
  mutedTextColor: '#64748b',
  titleColor: '#121212',
  taglineColor: '#64748b',
  inputBackgroundColor: '#ffffff',
  inputTextColor: '#0f172a',
  sendButtonBgColor: '#6190ff',
  sendButtonTextColor: '#ffffff',
  pageBackgroundColor: '#f8fafc',
  cardBackgroundColor: '#ffffff',
  
  // Layout
  chatWidth: '68rem',
  chatHeight: '72vh',
  bubbleMaxWidth: 60,
  cardRadius: '18px',
  cardOpacity: 90,
  messageSpacing: 16,
  inputHeight: 48,
  inputRadius: '12px',
  
  // Bubble styles
  bubbleRadius: '18px',
  bubblePadding: 12,
  aiBubbleBg: '#7b8ee5',
  aiTextColor: '#121212',
  aiOpacity: 1.0,
  aiBorderColor: '',
  aiBorderWidth: 0,
  userBubbleBg: '#3cddc2',
  userTextColor: '#111111',
  userOpacity: 1.0,
  userBorderColor: '',
  userBorderWidth: 0,
  
  // Avatar
  avatarSize: 40,
  avatarPosition: 'left',
  avatarShape: 'circle',
  showAvatarOnMobile: true,
  userAvatarSize: 40,
  userAvatarPosition: 'right',
  userAvatarShape: 'circle',
  showUserAvatarOnMobile: true,
  
  // Shadows
  enableShadow: true,
  shadowColor: '#000000',
  shadowBlur: 10,
  shadowOpacity: 15,
  
  // Audio
  showAudioControls: true,
  ttsAutoPlay: false,
  
  // AI/LLM
  aiModel: 'gpt-4o-mini',
  aiTemperature: 0.7,
  aiMaxTokens: 900,
  aiTopK: 8,
  aiStrictness: 'balanced' as const,
  aiSystemPrompt: 'You are a helpful AI assistant.',
  aiStreamResponses: true,
  aiRetainContext: true,
};

export default function AdminBranding() {
  const [form, setForm] = useState<Branding>(DEFAULTS);
  // const [loaded, setLoaded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [autoSave, setAutoSave] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('basic');
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const auth = localStorage.getItem('adminAuth') || '';
  
  // Load initial branding settings and merge with defaults
  useEffect(() => {
    const loadBranding = async () => {
      try {
        const data = await getAdminBranding(auth);
        // Merge server data with defaults so every field has a real value
        setForm({ ...DEFAULTS, ...data });
        // setLoaded(true);
      } catch (err) {
        setError('Failed to load branding settings');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadBranding();
  }, [auth]);

  // Update form value with immutable updates
  const updateForm = (key: keyof Branding, value: any) => {
    setForm(f => {
      const newForm = { ...f, [key]: value };
      debouncedSave(newForm);
      return newForm;
    });
  };

  // Debounced save function - saves full merged object
  const debouncedSave = (formData: Branding) => {
    if (!autoSave) return;

    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    saveTimeoutRef.current = setTimeout(async () => {
      try {
        setSaving(true);
        await putAdminBranding(auth, formData);
        setSuccessMessage('Settings saved automatically');
        setTimeout(() => setSuccessMessage(null), 2000);
      } catch (err) {
        setError('Auto-save failed');
        console.error(err);
      } finally {
        setSaving(false);
      }
    }, 800);
  };

  // Manual save
  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      await putAdminBranding(auth, form);
      setSuccessMessage('Settings saved successfully!');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError('Failed to save settings');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  // Create style mapper for preview
  const styleMapper = new BrandingStyleMapper(form);

  if (loading) {
    return (
      <div className="min-h-screen p-6 bg-zinc-100 flex items-center justify-center">
        <div className="text-slate-600">Loading branding settings...</div>
      </div>
    );
  }

  const tabs = [
    { id: 'basic', label: 'Basic Info' },
    { id: 'typography', label: 'Typography' },
    { id: 'colors', label: 'Colors' },
    { id: 'bubbles', label: 'Chat Bubbles' },
    { id: 'layout', label: 'Layout' },
    { id: 'backgrounds', label: 'Backgrounds' },
    { id: 'shadows', label: 'Shadows & Effects' },
    { id: 'avatar', label: 'Avatar' },
    { id: 'audio', label: 'Audio' },
    { id: 'llm', label: 'LLM Settings' },
  ];

  return (
    <div className="min-h-screen p-6 bg-zinc-100">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg mb-6 p-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-semibold text-slate-900">Branding Settings</h1>
              <p className="text-sm text-slate-600 mt-1">
                Customize your chatbot's appearance and behavior
              </p>
            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={autoSave}
                  onChange={(e) => setAutoSave(e.target.checked)}
                  className="rounded border-slate-300"
                />
                Update Live
              </label>
              <button
                onClick={handleSave}
                disabled={saving || autoSave}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
          
          {/* Status Messages */}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}
          {successMessage && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
              {successMessage}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Settings Panel */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl shadow-lg">
              {/* Tab Navigation */}
              <div className="border-b border-slate-200 p-1">
                <nav className="flex flex-wrap gap-1">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                        activeTab === tab.id
                          ? 'bg-indigo-100 text-indigo-700'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </nav>
              </div>

              {/* Tab Content */}
              <div className="p-6 max-h-[70vh] overflow-y-auto">
                {activeTab === 'basic' && <BasicInfoTab branding={form} updateBranding={updateForm} />}
                {activeTab === 'typography' && <TypographyTab branding={form} updateBranding={updateForm} />}
                {activeTab === 'colors' && <ColorsTab branding={form} updateBranding={updateForm} />}
                {activeTab === 'bubbles' && <BubblesTab branding={form} updateBranding={updateForm} />}
                {activeTab === 'layout' && <LayoutTab branding={form} updateBranding={updateForm} />}
                {activeTab === 'backgrounds' && <BackgroundsTab branding={form} updateBranding={updateForm} />}
                {activeTab === 'shadows' && <ShadowsTab branding={form} updateBranding={updateForm} />}
                {activeTab === 'avatar' && <AvatarTab branding={form} updateBranding={updateForm} />}
                {activeTab === 'audio' && <AudioTab branding={form} updateBranding={updateForm} />}
                {activeTab === 'llm' && <LLMTab branding={form} updateBranding={updateForm} />}
              </div>
            </div>
          </div>

          {/* Live Preview */}
          <div className="lg:col-span-1">
            <LivePreview styleMapper={styleMapper} branding={form} />
          </div>
        </div>
      </div>
    </div>
  );
}

// Form Input Components
const FormGroup = ({ label, children }: { label: string; children: React.ReactNode }) => (
  <div className="space-y-2">
    <label className="block text-sm font-medium text-slate-700">{label}</label>
    {children}
  </div>
);

const TextInput = ({
  value,
  onChange,
  placeholder
}: {
  value?: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) => (
  <input
    type="text"
    value={value ?? ''}
    onChange={(e) => onChange(e.target.value)}
    placeholder={placeholder}
    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
  />
);

type NumberInputProps = {
  value?: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
};

const NumberInput = ({ value, onChange, min, max, step = 1 }: NumberInputProps) => (
  <input
    type="number"
    value={value ?? ''}
    onChange={(e) => {
      const v = e.target.value;
      onChange(v === '' ? (undefined as unknown as number) : Number(v));
    }}
    min={min}
    max={max}
    step={step}
    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
  />
);


const ColorInput = ({
  value,
  onChange
}: {
  value?: string;
  onChange: (value: string) => void;
}) => (
  <div className="flex gap-2">
    <input
      type="color"
      value={value || '#000000'}
      onChange={(e) => onChange(e.target.value)}
      className="w-12 h-10 border border-slate-300 rounded cursor-pointer"
    />
    <input
      type="text"
      value={value ?? ''} // keep just one value prop
      onChange={(e) => onChange(e.target.value)}
      placeholder="#000000"
      className="flex-1 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
    />
  </div>
);

const CheckboxInput = ({
  checked,
  onChange,
  label
}: {
  checked?: boolean;
  onChange: (checked: boolean) => void;
  label: string;
}) => (
  <label className="flex items-center gap-2 text-sm">
    <input
      type="checkbox"
      checked={checked || false}
      onChange={(e) => onChange(e.target.checked)}
      className="rounded border-slate-300"
    />
    {label}
  </label>
);

const SelectInput = ({
  value,
  onChange,
  options
}: {
  value?: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
}) => (
  <select
    value={value ?? ''} // keep just one value prop
    onChange={(e) => onChange(e.target.value)}
    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
  >
    {options.map((option) => (
      <option key={option.value} value={option.value}>
        {option.label}
      </option>
    ))}
  </select>
);


// Tab Components
const BasicInfoTab = ({ branding, updateBranding }: { branding: Partial<Branding>; updateBranding: (key: keyof Branding, value: any) => void }) => (
  <div className="space-y-6">
    <FormGroup label="Company Name">
      <TextInput
        value={branding.companyName ?? ''}
        onChange={(value) => updateBranding('companyName', value)}
        placeholder="Company Chat"
      />
    </FormGroup>
    
    <FormGroup label="Tagline Text">
      <TextInput
        value={branding.taglineText ?? ''}
        onChange={(value) => updateBranding('taglineText', value)}
        placeholder="Ask questions about your company documents."
      />
    </FormGroup>
    
    <FormGroup label="Empty State Text">
      <TextInput
        value={branding.emptyStateText ?? ''}
        onChange={(value) => updateBranding('emptyStateText', value)}
        placeholder='Start by asking something like "What is the company dress code?"'
      />
    </FormGroup>
    
    <FormGroup label="Input Placeholder">
      <TextInput
        value={branding.inputPlaceholder ?? ''}
        onChange={(value) => updateBranding('inputPlaceholder', value)}
        placeholder="Type your question and press Enter…"
      />
    </FormGroup>
    
    <FormGroup label="Logo Data URL">
      <TextInput
        value={branding.logoDataUrl || ''}
        onChange={(value) => updateBranding('logoDataUrl', value)}
        placeholder="data:image/... or https://..."
      />
    </FormGroup>
    
    <FormGroup label="Favicon URL">
      <TextInput
        value={branding.faviconUrl || ''}
        onChange={(value) => updateBranding('faviconUrl', value)}
        placeholder="https://..."
      />
    </FormGroup>
  </div>
);

const TypographyTab = ({ branding, updateBranding }: { branding: Partial<Branding>; updateBranding: (key: keyof Branding, value: any) => void }) => (
  <div className="space-y-6">
    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">General Typography</h3>
      <div className="space-y-4">
        <FormGroup label="Font Family">
          <TextInput
            value={branding.fontFamily}
            onChange={(value) => updateBranding('fontFamily', value)}
            placeholder="system-ui, sans-serif"
          />
        </FormGroup>

        {/* New: handy presets that write to the same key */}
        <FormGroup label="Quick Font Preset">
          <SelectInput
            value={branding.fontFamily}
            onChange={(value) => updateBranding('fontFamily', value)}
            options={[
              { value: 'system-ui, sans-serif', label: 'System Default' },
              { value: 'Inter, sans-serif', label: 'Inter' },
              { value: 'Roboto, sans-serif', label: 'Roboto' },
              { value: '"Open Sans", sans-serif', label: 'Open Sans' },
              { value: 'Lora, serif', label: 'Lora' },
              { value: '"Playfair Display", serif', label: 'Playfair Display' },
            ]}
          />
        </FormGroup>
        
        <FormGroup label="Body Font Size (px)">
          <NumberInput
            value={branding.bodyFontSize}
            onChange={(value) => updateBranding('bodyFontSize', value)}
            min={10}
            max={24}
          />
        </FormGroup>
      </div>
    </div>
    
    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">Title Styling</h3>
      <div className="grid grid-cols-2 gap-4">
        <FormGroup label="Font Size (px)">
          <NumberInput
            value={branding.titleFontSize}
            onChange={(value) => updateBranding('titleFontSize', value)}
            min={12}
            max={48}
          />
        </FormGroup>
        
        <FormGroup label="Color">
          <ColorInput
            value={branding.titleColor}
            onChange={(value) => updateBranding('titleColor', value)}
          />
        </FormGroup>
        
        <div>
          <CheckboxInput
            checked={branding.titleBold}
            onChange={(value) => updateBranding('titleBold', value)}
            label="Bold"
          />
        </div>
        
        <div>
          <CheckboxInput
            checked={branding.titleItalic}
            onChange={(value) => updateBranding('titleItalic', value)}
            label="Italic"
          />
        </div>
      </div>
    </div>
    
    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">Tagline Styling</h3>
      <div className="grid grid-cols-2 gap-4">
        <FormGroup label="Font Size (px)">
          <NumberInput
            value={branding.taglineFontSize}
            onChange={(value) => updateBranding('taglineFontSize', value)}
            min={10}
            max={24}
          />
        </FormGroup>
        
        <FormGroup label="Color">
          <ColorInput
            value={branding.taglineColor}
            onChange={(value) => updateBranding('taglineColor', value)}
          />
        </FormGroup>
        
        <div>
          <CheckboxInput
            checked={branding.taglineBold}
            onChange={(value) => updateBranding('taglineBold', value)}
            label="Bold"
          />
        </div>
        
        <div>
          <CheckboxInput
            checked={branding.taglineItalic}
            onChange={(value) => updateBranding('taglineItalic', value)}
            label="Italic"
          />
        </div>
      </div>
    </div>
    
    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">Input Field Typography</h3>
      <div className="grid grid-cols-2 gap-4">
        <FormGroup label="Font Size (px)">
          <NumberInput
            value={branding.inputFontSize}
            onChange={(value) => updateBranding('inputFontSize', value)}
            min={10}
            max={20}
          />
        </FormGroup>
        
        <div className="space-y-2">
          <CheckboxInput
            checked={branding.inputBold}
            onChange={(value) => updateBranding('inputBold', value)}
            label="Bold"
          />
          <CheckboxInput
            checked={branding.inputItalic}
            onChange={(value) => updateBranding('inputItalic', value)}
            label="Italic"
          />
        </div>
      </div>
    </div>
  </div>
);

// Enhanced ColorsTab with granular controls
const ColorsTab = ({
  branding,
  updateBranding,
}: {
  branding: Partial<Branding>;
  updateBranding: (key: keyof Branding, value: any) => void;
}) => (
  <div className="space-y-6">
    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">Theme Colors</h3>
      <div className="grid grid-cols-2 gap-4">
        <FormGroup label="Primary Color">
          <ColorInput
            value={branding.primaryColor}
            onChange={(v) => updateBranding('primaryColor', v)}
          />
        </FormGroup>
        <FormGroup label="Accent Color">
          <ColorInput
            value={branding.accentColor}
            onChange={(v) => updateBranding('accentColor', v)}
          />
        </FormGroup>
      </div>
    </div>

    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">Text Colors</h3>
      <div className="grid grid-cols-2 gap-4">
        <FormGroup label="Main Text Color">
          <ColorInput
            value={branding.textColor}
            onChange={(v) => updateBranding('textColor', v)}
          />
        </FormGroup>
        <FormGroup label="Muted Text Color">
          <ColorInput
            value={branding.mutedTextColor}
            onChange={(v) => updateBranding('mutedTextColor', v)}
          />
        </FormGroup>
        <FormGroup label="Title Color">
          <ColorInput
            value={branding.titleColor}
            onChange={(v) => updateBranding('titleColor', v)}
          />
        </FormGroup>
        <FormGroup label="Tagline Color">
          <ColorInput
            value={branding.taglineColor}
            onChange={(v) => updateBranding('taglineColor', v)}
          />
        </FormGroup>
      </div>
    </div>

    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">Input Field Colors</h3>
      <div className="grid grid-cols-2 gap-4">
        <FormGroup label="Input Background">
          <ColorInput
            value={branding.inputBackgroundColor}
            onChange={(v) => updateBranding('inputBackgroundColor', v)}
          />
        </FormGroup>
        <FormGroup label="Input Text">
          <ColorInput
            value={branding.inputTextColor}
            onChange={(v) => updateBranding('inputTextColor', v)}
          />
        </FormGroup>
      </div>
    </div>

    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">Button Colors</h3>
      <div className="grid grid-cols-2 gap-4">
        <FormGroup label="Send Button Background">
          <ColorInput
            value={branding.sendButtonBgColor}
            onChange={(v) => updateBranding('sendButtonBgColor', v)}
          />
        </FormGroup>
        <FormGroup label="Send Button Text">
          <ColorInput
            value={branding.sendButtonTextColor}
            onChange={(v) => updateBranding('sendButtonTextColor', v)}
          />
        </FormGroup>
      </div>
    </div>

    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">Background Colors</h3>
      <div className="grid grid-cols-2 gap-4">
        <FormGroup label="Page Background">
          <ColorInput
            value={branding.pageBackgroundColor}
            onChange={(v) => updateBranding('pageBackgroundColor', v)}
          />
        </FormGroup>
        <FormGroup label="Card Background">
          <ColorInput
            value={branding.cardBackgroundColor}
            onChange={(v) => updateBranding('cardBackgroundColor', v)}
          />
        </FormGroup>
      </div>
    </div>
  </div>
);

// Enhanced BubblesTab with opacity controls
const BubblesTab = ({
  branding,
  updateBranding,
}: {
  branding: Partial<Branding>;
  updateBranding: (key: keyof Branding, value: any) => void;
}) => (
  <div className="space-y-6">
    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">Bubble Layout</h3>
      <div className="grid grid-cols-2 gap-4">
        <FormGroup label="Bubble Radius (CSS)">
          <TextInput
            value={branding.bubbleRadius?.toString()}
            onChange={(v) => updateBranding('bubbleRadius', v)}
            placeholder="1rem"
          />
        </FormGroup>
        <FormGroup label="Bubble Padding (px)">
          <NumberInput
            value={branding.bubblePadding}
            onChange={(v) => updateBranding('bubblePadding', v)}
            min={0}
            max={48}
          />
        </FormGroup>
        <FormGroup label="Bubble Max Width (CSS)">
          <TextInput
            value={branding.bubbleMaxWidth?.toString()}
            onChange={(v) => updateBranding('bubbleMaxWidth', v)}
            placeholder="42rem"
          />
        </FormGroup>
        <FormGroup label="Message Spacing (px)">
          <NumberInput
            value={branding.messageSpacing}
            onChange={(v) => updateBranding('messageSpacing', v)}
            min={0}
            max={50}
          />
        </FormGroup>
      </div>
    </div>

    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">AI Assistant Bubble</h3>
      <div className="grid grid-cols-2 gap-4">
        <FormGroup label="Background Color">
          <ColorInput
            value={branding.aiBubbleBg}
            onChange={(v) => updateBranding('aiBubbleBg', v)}
          />
        </FormGroup>
        <FormGroup label="Text Color">
          <ColorInput
            value={branding.aiTextColor}
            onChange={(v) => updateBranding('aiTextColor', v)}
          />
        </FormGroup>
        <FormGroup label="Opacity (0-100%)">
          <NumberInput
            value={floatToPct(branding.aiOpacity)}
            onChange={(v) => updateBranding('aiOpacity', pctToFloat(v))}
            min={0}
            max={100}
          />
        </FormGroup>
        <FormGroup label="Border Color">
          <ColorInput
            value={branding.aiBorderColor}
            onChange={(v) => updateBranding('aiBorderColor', v)}
          />
        </FormGroup>
        <FormGroup label="Border Width (px)">
          <NumberInput
            value={branding.aiBorderWidth}
            onChange={(v) => updateBranding('aiBorderWidth', v)}
            min={0}
            max={10}
          />
        </FormGroup>
      </div>
    </div>

    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">User Bubble</h3>
      <div className="grid grid-cols-2 gap-4">
        <FormGroup label="Background Color">
          <ColorInput
            value={branding.userBubbleBg}
            onChange={(v) => updateBranding('userBubbleBg', v)}
          />
        </FormGroup>
        <FormGroup label="Text Color">
          <ColorInput
            value={branding.userTextColor}
            onChange={(v) => updateBranding('userTextColor', v)}
          />
        </FormGroup>
        <FormGroup label="Opacity (0-100%)">
          <NumberInput
            value={floatToPct(branding.userOpacity)}
            onChange={(v) => updateBranding('userOpacity', pctToFloat(v))}
            min={0}
            max={100}
          />
        </FormGroup>
        <FormGroup label="Border Color">
          <ColorInput
            value={branding.userBorderColor}
            onChange={(v) => updateBranding('userBorderColor', v)}
          />
        </FormGroup>
        <FormGroup label="Border Width (px)">
          <NumberInput
            value={branding.userBorderWidth}
            onChange={(v) => updateBranding('userBorderWidth', v)}
            min={0}
            max={10}
          />
        </FormGroup>
      </div>
    </div>
  </div>
);

/* --- The remainder of the file (Colors, Bubbles, Layout, Backgrounds, Shadows, Avatar, Audio, LLM, LivePreview) is unchanged from your version --- */
// (Keeping all existing controls; these send the flat keys that are now whitelisted + persisted in the backend.)
// ... (rest of your original component content from ColorsTab to LivePreview stays identical) ...
const LayoutTab = ({ branding, updateBranding }: { branding: Partial<Branding>; updateBranding: (key: keyof Branding, value: any) => void }) => (
  <div className="space-y-6">
    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">Chat Container</h3>
      <div className="grid grid-cols-2 gap-4">
        <FormGroup label="Chat Width">
          <TextInput
            value={branding.chatWidth?.toString()}
            onChange={(value) => updateBranding('chatWidth', value)}
            placeholder="64rem"
          />
        </FormGroup>
        
        <FormGroup label="Chat Height">
          <TextInput
            value={branding.chatHeight?.toString()}
            onChange={(value) => updateBranding('chatHeight', value)}
            placeholder="60vh"
          />
        </FormGroup>
        
        <FormGroup label="Chat Offset Top (px)">
          <NumberInput
            value={typeof branding.chatOffsetTop === 'number' ? branding.chatOffsetTop : undefined}
            onChange={(value) => updateBranding('chatOffsetTop', value)}
            min={0}
            max={100}
          />
        </FormGroup>
      </div>
    </div>
    
    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">Card Styling</h3>
      <div className="grid grid-cols-2 gap-4">
        <FormGroup label="Border Radius">
          <TextInput
            value={branding.cardRadius?.toString()}
            onChange={(value) => updateBranding('cardRadius', value)}
            placeholder="1rem"
          />
        </FormGroup>
        
        <FormGroup label="Padding (px)">
          <NumberInput
            value={branding.cardPadding}
            onChange={(value) => updateBranding('cardPadding', value)}
            min={0}
            max={48}
          />
        </FormGroup>
        
        <FormGroup label="Opacity (%)">
          <NumberInput
            value={branding.cardOpacity}
            onChange={(value) => updateBranding('cardOpacity', value)}
            min={0}
            max={100}
          />
        </FormGroup>
      </div>
    </div>
    
    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">Input Field</h3>
      <div className="grid grid-cols-2 gap-4">
        <FormGroup label="Height (px)">
          <NumberInput
            value={branding.inputHeight}
            onChange={(value) => updateBranding('inputHeight', value)}
            min={32}
            max={80}
          />
        </FormGroup>
        
        <FormGroup label="Border Radius">
          <TextInput
            value={branding.inputRadius?.toString()}
            onChange={(value) => updateBranding('inputRadius', value)}
            placeholder="0.75rem"
          />
        </FormGroup>
      </div>
    </div>
  </div>
);

const BackgroundsTab = ({ branding, updateBranding }: { branding: Partial<Branding>; updateBranding: (key: keyof Branding, value: any) => void }) => (
  <div className="space-y-6">
    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">Page Background</h3>
      <div className="space-y-4">
        <FormGroup label="Background Color">
          <ColorInput
            value={branding.pageBackgroundColor}
            onChange={(value) => updateBranding('pageBackgroundColor', value)}
          />
        </FormGroup>
        
        <FormGroup label="Background Image URL">
          <TextInput
            value={branding.pageBackgroundUrl || ''}
            onChange={(value) => updateBranding('pageBackgroundUrl', value)}
            placeholder="https://... or data:image/..."
          />
        </FormGroup>
      </div>
    </div>
    
    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">Card Background</h3>
      <div className="space-y-4">
        <FormGroup label="Background Color">
          <ColorInput
            value={branding.cardBackgroundColor}
            onChange={(value) => updateBranding('cardBackgroundColor', value)}
          />
        </FormGroup>
        
        <FormGroup label="Background Image URL">
          <TextInput
            value={branding.cardBackgroundUrl || ''}
            onChange={(value) => updateBranding('cardBackgroundUrl', value)}
            placeholder="https://... or data:image/..."
          />
        </FormGroup>
        
        <FormGroup label="CSS Override">
          <TextInput
            value={branding.cardBackgroundCssOverride}
            onChange={(value) => updateBranding('cardBackgroundCssOverride', value)}
            placeholder="linear-gradient(...) or custom CSS"
          />
        </FormGroup>
      </div>
    </div>
  </div>
);

const ShadowsTab = ({ branding, updateBranding }: { branding: Partial<Branding>; updateBranding: (key: keyof Branding, value: any) => void }) => (
  <div className="space-y-6">
    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">Shadow Settings</h3>
      <div className="space-y-4">
        <CheckboxInput
          checked={branding.enableShadow}
          onChange={(value) => updateBranding('enableShadow', value)}
          label="Enable Shadow"
        />
        
        <div className="grid grid-cols-2 gap-4">
          <FormGroup label="Shadow Color">
            <ColorInput
              value={branding.shadowColor}
              onChange={(value) => updateBranding('shadowColor', value)}
            />
          </FormGroup>
          
          <FormGroup label="Shadow Opacity (%)">
            <NumberInput
              value={branding.shadowOpacity}
              onChange={(value) => updateBranding('shadowOpacity', value)}
              min={0}
              max={100}
            />
          </FormGroup>
          
          <FormGroup label="Shadow Blur (px)">
            <NumberInput
              value={branding.shadowBlur}
              onChange={(value) => updateBranding('shadowBlur', value)}
              min={0}
              max={50}
            />
          </FormGroup>
          
          <FormGroup label="Shadow Spread (px)">
            <NumberInput
              value={branding.shadowSpread}
              onChange={(value) => updateBranding('shadowSpread', value)}
              min={0}
              max={20}
            />
          </FormGroup>
        </div>
      </div>
    </div>
    
    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">Glow Effect</h3>
      <div className="space-y-4">
        <CheckboxInput
          checked={branding.enableGlow}
          onChange={(value) => updateBranding('enableGlow', value)}
          label="Enable Glow"
        />
        
        <div className="grid grid-cols-2 gap-4">
          <FormGroup label="Glow Color">
            <ColorInput
              value={branding.glowColor}
              onChange={(value) => updateBranding('glowColor', value)}
            />
          </FormGroup>
          
          <FormGroup label="Glow Opacity (%)">
            <NumberInput
              value={branding.glowOpacity}
              onChange={(value) => updateBranding('glowOpacity', value)}
              min={0}
              max={100}
            />
          </FormGroup>
          
          <FormGroup label="Glow Blur (px)">
            <NumberInput
              value={branding.glowBlur}
              onChange={(value) => updateBranding('glowBlur', value)}
              min={0}
              max={50}
            />
          </FormGroup>
        </div>
      </div>
    </div>
  </div>
);

const AvatarTab = ({ branding, updateBranding }: { branding: Partial<Branding>; updateBranding: (key: keyof Branding, value: any) => void }) => (
  <div className="space-y-6">
    <FormGroup label="Avatar Image URL">
      <TextInput
        value={branding.avatarImageUrl || ''}
        onChange={(value) => updateBranding('avatarImageUrl', value)}
        placeholder="https://... or data:image/..."
      />
    </FormGroup>
    
    <div className="grid grid-cols-2 gap-4">
      <FormGroup label="Avatar Size (px)">
        <NumberInput
          value={branding.avatarSize}
          onChange={(value) => updateBranding('avatarSize', value)}
          min={20}
          max={80}
        />
      </FormGroup>
      
      <FormGroup label="Avatar Position">
        <SelectInput
          value={branding.avatarPosition}
          onChange={(value) => updateBranding('avatarPosition', value)}
          options={[
            { value: 'left', label: 'Left' },
            { value: 'right', label: 'Right' },
            { value: 'none', label: 'Hidden' },
          ]}
        />
      </FormGroup>
      
      <FormGroup label="Avatar Shape">
        <SelectInput
          value={branding.avatarShape}
          onChange={(value) => updateBranding('avatarShape', value)}
          options={[
            { value: 'circle', label: 'Circle' },
            { value: 'rounded', label: 'Rounded' },
            { value: 'square', label: 'Square' },
          ]}
        />
      </FormGroup>
      
      <div className="pt-6">
        <CheckboxInput
          checked={branding.showAvatarOnMobile}
          onChange={(value) => updateBranding('showAvatarOnMobile', value)}
          label="Show on Mobile"
        />
      </div>
    </div>
    
    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">User Avatar</h3>
      <FormGroup label="User Avatar Image URL">
        <TextInput
          value={branding.userAvatarImageUrl || ''}
          onChange={(value) => updateBranding('userAvatarImageUrl', value)}
          placeholder="https://... or data:image/..."
        />
      </FormGroup>
      
      <div className="grid grid-cols-2 gap-4">
        <FormGroup label="Avatar Size (px)">
          <NumberInput
            value={branding.userAvatarSize ?? 40}
            onChange={(value) => updateBranding('userAvatarSize', value)}
            min={20}
            max={80}
          />
        </FormGroup>
        
        <FormGroup label="Avatar Position">
          <SelectInput
            value={branding.userAvatarPosition ?? 'right'}
            onChange={(value) => updateBranding('userAvatarPosition', value)}
            options={[
              { value: 'left', label: 'Left' },
              { value: 'right', label: 'Right' },
            ]}
          />
        </FormGroup>
        
        <FormGroup label="Avatar Shape">
          <SelectInput
            value={branding.userAvatarShape ?? 'circle'}
            onChange={(value) => updateBranding('userAvatarShape', value)}
            options={[
              { value: 'circle', label: 'Circle' },
              { value: 'rounded', label: 'Rounded' },
              { value: 'square', label: 'Square' },
            ]}
          />
        </FormGroup>
      </div>
      
      <div className="pt-6">
        <CheckboxInput
          checked={branding.showUserAvatarOnMobile ?? true}
          onChange={(value) => updateBranding('showUserAvatarOnMobile', value)}
          label="Show on Mobile"
        />
      </div>
    </div>
  </div>
);

const AudioTab = ({ branding, updateBranding }: { branding: Partial<Branding>; updateBranding: (key: keyof Branding, value: any) => void }) => (
  <div className="space-y-6">
    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">Text-to-Speech</h3>
      <div className="space-y-4">
        <CheckboxInput
          checked={branding.enableTextToSpeech}
          onChange={(value) => updateBranding('enableTextToSpeech', value)}
          label="Enable Text-to-Speech"
        />
        
        <div className="grid grid-cols-2 gap-4">
          <FormGroup label="Voice">
            <TextInput
              value={branding.ttsVoice}
              onChange={(value) => updateBranding('ttsVoice', value)}
              placeholder="default"
            />
          </FormGroup>
          
          <FormGroup label="Speed">
            <NumberInput
              value={branding.ttsSpeed}
              onChange={(value) => updateBranding('ttsSpeed', value)}
              min={0.5}
              max={2}
              step={0.1}
            />
          </FormGroup>
        </div>
        
        <CheckboxInput
          checked={branding.ttsAutoPlay}
          onChange={(value) => updateBranding('ttsAutoPlay', value)}
          label="Auto-play responses"
        />
      </div>
    </div>
    
    <div>
      <h3 className="text-lg font-medium text-slate-900 mb-4">Speech-to-Text</h3>
      <div className="space-y-4">
        <CheckboxInput
          checked={branding.enableSpeechToText}
          onChange={(value) => updateBranding('enableSpeechToText', value)}
          label="Enable Speech-to-Text"
        />
        
        <div className="grid grid-cols-2 gap-4">
          <FormGroup label="Language">
            <TextInput
              value={branding.sttLanguage}
              onChange={(value) => updateBranding('sttLanguage', value)}
              placeholder="en-US"
            />
          </FormGroup>
          
          <div className="pt-6">
            <CheckboxInput
              checked={branding.sttAutoSend}
              onChange={(value) => updateBranding('sttAutoSend', value)}
              label="Auto-send after speech"
            />
          </div>
        </div>
      </div>
    </div>
    
    <CheckboxInput
      checked={branding.showAudioControls}
      onChange={(value) => updateBranding('showAudioControls', value)}
      label="Show audio controls"
    />
  </div>
);

const LLMTab = ({ branding, updateBranding }: { branding: Partial<Branding>; updateBranding: (key: keyof Branding, value: any) => void }) => (
  <div className="space-y-6">
    <div className="grid grid-cols-2 gap-4">
      <FormGroup label="AI Model">
        <TextInput
          value={branding.aiModel}
          onChange={(value) => updateBranding('aiModel', value)}
          placeholder="gpt-4"
        />
      </FormGroup>
      
      <FormGroup label="Temperature">
        <NumberInput
          value={branding.aiTemperature}
          onChange={(value) => updateBranding('aiTemperature', value)}
          min={0}
          max={2}
          step={0.1}
        />
      </FormGroup>
      
      <FormGroup label="Max Tokens">
        <NumberInput
          value={branding.aiMaxTokens}
          onChange={(value) => updateBranding('aiMaxTokens', value)}
          min={1}
          max={8192}
        />
      </FormGroup>
      
      <FormGroup label="Top K">
        <NumberInput
          value={branding.aiTopK}
          onChange={(value) => updateBranding('aiTopK', value)}
          min={1}
          max={100}
        />
      </FormGroup>
      
      <FormGroup label="Strictness">
        <SelectInput
          value={branding.aiStrictness}
          onChange={(value) => updateBranding('aiStrictness', value)}
          options={[
            { value: 'creative', label: 'Creative' },
            { value: 'balanced', label: 'Balanced' },
            { value: 'precise', label: 'Precise' },
          ]}
        />
      </FormGroup>
    </div>
    
    <FormGroup label="System Prompt">
      <textarea
        value={branding.aiSystemPrompt || ''}
        onChange={(e) => updateBranding('aiSystemPrompt', e.target.value)}
        rows={4}
        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        placeholder="You are a helpful AI assistant."
      />
    </FormGroup>
    
    <div className="space-y-2">
      <CheckboxInput
        checked={branding.aiStreamResponses}
        onChange={(value) => updateBranding('aiStreamResponses', value)}
        label="Stream responses"
      />
      <CheckboxInput
        checked={branding.aiRetainContext}
        onChange={(value) => updateBranding('aiRetainContext', value)}
        label="Retain conversation context"
      />
    </div>
  </div>
);

// Live Preview Component
const LivePreview = ({ styleMapper, branding }: { styleMapper: BrandingStyleMapper; branding: Partial<Branding> }) => {
  const pageStyle = styleMapper.getPageStyle();
  const cardStyle = styleMapper.getCardStyle();
  const titleStyle = styleMapper.getTitleStyle();
  const taglineStyle = styleMapper.getTaglineStyle();
  const inputStyle = styleMapper.getInputStyle();
  const buttonStyle = styleMapper.getButtonStyle();
  const userBubbleStyle = styleMapper.getBubbleStyle('user');
  const aiBubbleStyle = styleMapper.getBubbleStyle('assistant');
  const assistantAvatarStyle = styleMapper.getAvatarStyle('assistant');
  const userAvatarStyle = styleMapper.getAvatarStyle('user');

  return (
    <div className="bg-white rounded-2xl shadow-lg sticky top-6">
      <div className="p-4 border-b border-slate-200">
        <h3 className="text-lg font-medium text-slate-900">Live Preview</h3>
      </div>
      
      <div className="p-4">
        <div className="border border-slate-200 rounded-lg overflow-hidden">
          {/* Mini page preview */}
          <div style={{...pageStyle, minHeight: '400px', padding: '16px'}} className="relative">
            <div style={cardStyle} className="mx-auto p-4">
              {/* Header */}
              <div className="text-center mb-4">
                <h1 style={titleStyle}>
                  {branding.companyName || 'Company Chat'}
                </h1>
                <p style={taglineStyle}>
                  {branding.taglineText || 'Ask questions about your company documents.'}
                </p>
              </div>
              
              {/* Sample conversation */}
              <div className="space-y-3 mb-4 min-h-[200px]">
                <div className="flex gap-2">
                  {styleMapper.shouldShowAvatar('assistant') && styleMapper.getAvatarPosition('assistant') === 'left' && (
                    <div style={assistantAvatarStyle} className="bg-slate-200 rounded-full flex-shrink-0 flex items-center justify-center text-xs text-slate-600">
                      {styleMapper.getAvatarImageUrl('assistant') ? (
                        <img src={styleMapper.getAvatarImageUrl('assistant')} alt="AI" style={assistantAvatarStyle} />
                      ) : 'AI'}
                    </div>
                  )}
                  <div style={aiBubbleStyle} className="text-sm">
                    Hello! How can I help you today?
                    <div className="mt-1 text-xs opacity-70">
                      <div>Sources:</div>
                      <div className="underline">company-handbook.pdf</div>
                    </div>
                  </div>
                  {styleMapper.shouldShowAvatar('assistant') && styleMapper.getAvatarPosition('assistant') === 'right' && (
                    <div style={assistantAvatarStyle} className="bg-slate-200 rounded-full flex-shrink-0 flex items-center justify-center text-xs text-slate-600">
                      {styleMapper.getAvatarImageUrl('assistant') ? (
                        <img src={styleMapper.getAvatarImageUrl('assistant')} alt="AI" style={assistantAvatarStyle} />
                      ) : 'AI'}
                    </div>
                  )}
                </div>
                
                <div className="flex gap-2 justify-end">
                  {styleMapper.shouldShowAvatar('user') && styleMapper.getAvatarPosition('user') === 'left' && (
                    <div style={userAvatarStyle} className="bg-slate-300 rounded-full flex-shrink-0 flex items-center justify-center text-xs text-slate-700">
                      {styleMapper.getAvatarImageUrl('user') ? (
                        <img src={styleMapper.getAvatarImageUrl('user')} alt="User" style={userAvatarStyle} />
                      ) : 'U'}
                    </div>
                  )}
                  <div style={userBubbleStyle} className="text-sm">
                    What are the company benefits?
                  </div>
                  {styleMapper.shouldShowAvatar('user') && styleMapper.getAvatarPosition('user') === 'right' && (
                    <div style={userAvatarStyle} className="bg-slate-300 rounded-full flex-shrink-0 flex items-center justify-center text-xs text-slate-700">
                      {styleMapper.getAvatarImageUrl('user') ? (
                        <img src={styleMapper.getAvatarImageUrl('user')} alt="User" style={userAvatarStyle} />
                      ) : 'U'}
                    </div>
                  )}
                </div>
                
                <div className="flex gap-2">
                  {styleMapper.shouldShowAvatar('assistant') && styleMapper.getAvatarPosition('assistant') === 'left' && (
                    <div style={assistantAvatarStyle} className="bg-slate-200 rounded-full flex-shrink-0 flex items-center justify-center text-xs text-slate-600">
                      {styleMapper.getAvatarImageUrl('assistant') ? (
                        <img src={styleMapper.getAvatarImageUrl('assistant')} alt="AI" style={assistantAvatarStyle} />
                      ) : 'AI'}
                    </div>
                  )}
                  <div style={aiBubbleStyle} className="text-sm">
                    We offer comprehensive health insurance, 401k matching, unlimited PTO, and professional development budget.
                  </div>
                </div>
              </div>
              
              {/* Input area */}
              <div className="flex gap-2">
                <input
                  style={inputStyle}
                  className="flex-1 outline-none"
                  placeholder={branding.inputPlaceholder || 'Type your question and press Enter…'}
                />
                <button
                  style={buttonStyle}
                  className="px-4 rounded-lg transition-colors"
                >
                  {styleMapper.getSendButtonText()}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
