import { useEffect, useState } from "react";
import { getCurrentTenant, fetchBranding, updateBranding } from "@/lib/api";
import { BrandingSettings, defaultBranding, applyBrandingToDOM } from "@/lib/theme";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { toast } from "@/hooks/use-toast";
import ImageInput from "@/lib/components/controls/ImageInput";
import ShadowControls from "@/lib/components/controls/ShadowControls";
import FontControls from "@/lib/components/controls/FontControls";
import RobotAvatar from "@/lib/components/RobotAvatar";

const AdminBrandingPage = () => {
  const [branding, setBranding] = useState<BrandingSettings>(defaultBranding);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const brandingData = await fetchBranding();
        setBranding(brandingData);
        applyBrandingToDOM(brandingData);
      } catch (error) {
        console.error("Failed to load branding:", error);
        // Use defaults if fetch fails
        setBranding(defaultBranding);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const saveBranding = async (updates: Partial<BrandingSettings>, msg = "Saved") => {
    const updated = { ...branding, ...updates };
    setBranding(updated);
    
    try {
      await updateBranding(updated);
      applyBrandingToDOM(updated);
      toast({ title: "Success", description: msg });
    } catch (error) {
      toast({ 
        title: "Error", 
        description: "Failed to save branding settings", 
        variant: "destructive" 
      });
    }
  };

  const handleSaveAll = async () => {
    try {
      await updateBranding(branding);
      applyBrandingToDOM(branding);
      toast({ title: "Success", description: "All changes saved" });
    } catch (error) {
      toast({ 
        title: "Error", 
        description: "Failed to save all changes", 
        variant: "destructive" 
      });
    }
  };

  if (loading) {
    return <div className="p-6 text-sm text-muted-foreground">Loading branding settings...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="rounded border p-3 w-[320px]">
          <div className="text-sm font-medium">Tenant Configuration</div>
          <div className="text-xs text-muted-foreground mt-2">Tenant ID</div>
          <div className="text-sm mt-1">{getCurrentTenant()}</div>
          <div className="text-xs text-muted-foreground mt-2">
            All API requests will use this tenant ID
          </div>
        </div>
        <Button variant="outline" onClick={handleSaveAll}>
          Save All
        </Button>
      </div>

      {/* Title & Basic Colors */}
      <Card className="p-5 space-y-4">
        <div className="text-lg font-semibold">Basic Branding</div>

        <div className="space-y-2">
          <Label>Application Title</Label>
          <Input
            value={branding.title || ""}
            onChange={(e) => saveBranding({ title: e.target.value }, "Title updated")}
            placeholder="e.g., LexaAI Company Chatbot"
          />
        </div>

        <div className="grid sm:grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label>Accent Color</Label>
            <Input
              type="color"
              value={branding.accentColor}
              onChange={(e) => saveBranding({ accentColor: e.target.value }, "Accent color updated")}
            />
          </div>
          <div className="space-y-2">
            <Label>Primary Color</Label>
            <Input
              type="color"
              value={branding.primaryColor}
              onChange={(e) => saveBranding({ primaryColor: e.target.value }, "Primary color updated")}
            />
          </div>
          <div className="space-y-2">
            <Label>Muted Text Color</Label>
            <Input
              type="color"
              value={branding.mutedTextColor}
              onChange={(e) => saveBranding({ mutedTextColor: e.target.value }, "Muted text updated")}
            />
          </div>
        </div>
      </Card>

      {/* Robot Configuration */}
      <Card className="p-5 space-y-4">
        <div className="text-lg font-semibold">Robot Avatar</div>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-4">
            <ImageInput
              label="Robot Image"
              value={branding.robot.imageUrl}
              onChange={(imageUrl) => saveBranding({ 
                robot: { ...branding.robot, imageUrl } 
              }, "Robot image updated")}
              placeholder="URL to robot image..."
            />
            
            <div className="space-y-2">
              <Label>Size ({branding.robot.size}px)</Label>
              <Slider
                value={[branding.robot.size]}
                onValueChange={([size]) => saveBranding({ 
                  robot: { ...branding.robot, size } 
                }, "Robot size updated")}
                max={256}
                min={32}
                step={8}
                className="w-full"
              />
            </div>
          </div>
          
          <div className="flex items-center justify-center p-4 border rounded-lg bg-muted/20">
            <RobotAvatar 
              size={Math.min(branding.robot.size, 128)}
              customSrc={branding.robot.imageUrl}
              accent={branding.accentColor}
              primary={branding.primaryColor}
            />
          </div>
        </div>
      </Card>

      {/* Glow & Shadow */}
      <Card className="p-5 space-y-4">
        <div className="text-lg font-semibold">Glow & Shadow Effects</div>
        <ShadowControls
          value={branding.shadow}
          onChange={(shadow) => saveBranding({ shadow }, "Shadow updated")}
        />
      </Card>

      {/* Background & Foreground */}
      <Card className="p-5 space-y-4">
        <div className="text-lg font-semibold">Background & Layout</div>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-4">
            <Label className="text-sm font-medium">Page Background</Label>
            <Input
              type="color"
              value={branding.background.color || "#ffffff"}
              onChange={(e) => saveBranding({ 
                background: { ...branding.background, color: e.target.value } 
              }, "Background color updated")}
            />
            <ImageInput
              label="Background Image (overrides color)"
              value={branding.background.imageUrl}
              onChange={(imageUrl) => saveBranding({ 
                background: { ...branding.background, imageUrl } 
              }, "Background image updated")}
            />
          </div>
          
          <div className="space-y-4">
            <Label className="text-sm font-medium">Chat Card Background</Label>
            <Input
              type="color"
              value={branding.foreground.color || "#ffffff"}
              onChange={(e) => saveBranding({ 
                foreground: { ...branding.foreground, color: e.target.value } 
              }, "Foreground color updated")}
            />
            <ImageInput
              label="Card Background Image (overrides color)"
              value={branding.foreground.imageUrl}
              onChange={(imageUrl) => saveBranding({ 
                foreground: { ...branding.foreground, imageUrl } 
              }, "Foreground image updated")}
            />
          </div>
        </div>
      </Card>

      {/* Text Styles */}
      <Card className="p-5 space-y-4">
        <div className="text-lg font-semibold">Text Styling</div>
        
        <FontControls
          label="Tagline Style"
          value={branding.tagline}
          onChange={(tagline) => saveBranding({ tagline }, "Tagline style updated")}
        />
        
        <FontControls
          label="Empty State Text Style"
          value={branding.emptyState}
          onChange={(emptyState) => saveBranding({ emptyState }, "Empty state style updated")}
        />
        
        <FontControls
          label="Input Placeholder Style"
          value={branding.placeholder}
          onChange={(placeholder) => saveBranding({ placeholder }, "Placeholder style updated")}
        />
      </Card>

      {/* Favicons */}
      <Card className="p-5 space-y-4">
        <div className="text-lg font-semibold">Favicons & Manifest</div>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>16x16 Favicon URL</Label>
            <Input
              type="url"
              value={branding.favicon?.url16 || ""}
              onChange={(e) => saveBranding({ 
                favicon: { ...branding.favicon, url16: e.target.value } 
              }, "16x16 favicon updated")}
              placeholder="https://example.com/favicon-16x16.png"
            />
          </div>
          
          <div className="space-y-2">
            <Label>32x32 Favicon URL</Label>
            <Input
              type="url"
              value={branding.favicon?.url32 || ""}
              onChange={(e) => saveBranding({ 
                favicon: { ...branding.favicon, url32: e.target.value } 
              }, "32x32 favicon updated")}
              placeholder="https://example.com/favicon-32x32.png"
            />
          </div>
          
          <div className="space-y-2">
            <Label>Apple Touch Icon URL</Label>
            <Input
              type="url"
              value={branding.favicon?.appleTouch || ""}
              onChange={(e) => saveBranding({ 
                favicon: { ...branding.favicon, appleTouch: e.target.value } 
              }, "Apple touch icon updated")}
              placeholder="https://example.com/apple-touch-icon.png"
            />
          </div>
          
          <div className="space-y-2">
            <Label>Manifest URL</Label>
            <Input
              type="url"
              value={branding.favicon?.manifestUrl || ""}
              onChange={(e) => saveBranding({ 
                favicon: { ...branding.favicon, manifestUrl: e.target.value } 
              }, "Manifest updated")}
              placeholder="https://example.com/site.webmanifest"
            />
          </div>
        </div>
      </Card>

      {/* Live Preview */}
      <Card className="p-5 space-y-4">
        <div className="text-lg font-semibold">Live Preview</div>
        <div 
          className="p-6 rounded-xl border lia-glow"
          style={{
            backgroundColor: branding.foreground.color,
            backgroundImage: branding.foreground.imageUrl ? `url(${branding.foreground.imageUrl})` : undefined,
            backgroundSize: 'cover',
            backgroundPosition: 'center'
          }}
        >
          <div className="text-center space-y-4">
            <h1 
              className="text-2xl font-bold"
              style={{
                fontFamily: branding.tagline.fontFamily,
                color: branding.tagline.color
              }}
            >
              {branding.title}
            </h1>
            
            <RobotAvatar 
              size={branding.robot.size}
              customSrc={branding.robot.imageUrl}
              accent={branding.accentColor}
              primary={branding.primaryColor}
            />
            
            <p 
              style={{
                fontFamily: branding.emptyState.fontFamily,
                fontSize: branding.emptyState.fontSize,
                color: branding.emptyState.color
              }}
            >
              Preview of your branded chat interface
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default AdminBrandingPage;
