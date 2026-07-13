"use client";
import { useState } from "react";
import { Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { AppSidebar } from "./app-sidebar";
export function MobileNavigation({ permissions }: { permissions?: string[] }) {
  const [open, setOpen] = useState(false);
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          aria-label="Open navigation"
        >
          <Menu />
        </Button>
      </DialogTrigger>
      <DialogContent
        title="Navigation"
        className="start-0 top-0 h-dvh w-72 max-w-none translate-x-0 translate-y-0 rounded-none p-0"
      >
        <AppSidebar
          permissions={permissions}
          className="w-full border-0"
          onNavigate={() => setOpen(false)}
        />
      </DialogContent>
    </Dialog>
  );
}
