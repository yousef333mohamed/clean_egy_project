import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const variants = cva(
  "inline-flex items-center justify-center gap-2 rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90",
        secondary:
          "bg-secondary px-4 py-2 text-secondary-foreground hover:bg-secondary/80",
        outline: "border border-border bg-background px-4 py-2 hover:bg-muted",
        ghost: "px-3 py-2 hover:bg-muted",
        destructive:
          "bg-destructive px-4 py-2 text-white hover:bg-destructive/90",
      },
      size: { default: "h-10", sm: "h-8 text-xs", icon: "size-10 p-0" },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);
export function Button({
  className,
  variant,
  size,
  asChild,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof variants> & { asChild?: boolean }) {
  const Component = asChild ? Slot : "button";
  return (
    <Component
      className={cn(variants({ variant, size }), className)}
      {...props}
    />
  );
}
