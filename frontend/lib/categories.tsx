import {
  Bell,
  Briefcase,
  Calendar,
  HelpCircle,
  Heart,
  LifeBuoy,
  type LucideIcon,
  Banknote,
  Newspaper,
  Package,
  Plane,
  ShieldAlert,
  Tag,
  Users,
} from "lucide-react";

// Icon + accent color per category slug, mirroring backend taxonomy.
export const CATEGORY_META: Record<string, { icon: LucideIcon; color: string }> = {
  work: { icon: Briefcase, color: "#2563eb" },
  finance: { icon: Banknote, color: "#059669" },
  shipping: { icon: Package, color: "#d97706" },
  travel: { icon: Plane, color: "#0891b2" },
  promotions: { icon: Tag, color: "#db2777" },
  social: { icon: Users, color: "#7c3aed" },
  newsletters: { icon: Newspaper, color: "#4f46e5" },
  updates: { icon: Bell, color: "#0d9488" },
  support: { icon: LifeBuoy, color: "#dc2626" },
  events: { icon: Calendar, color: "#ca8a04" },
  personal: { icon: Heart, color: "#e11d48" },
  spam: { icon: ShieldAlert, color: "#6b7280" },
  uncategorized: { icon: HelpCircle, color: "#94a3b8" },
};

export function categoryColor(slug: string): string {
  return CATEGORY_META[slug]?.color ?? "#94a3b8";
}
