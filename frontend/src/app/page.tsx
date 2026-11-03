import { ChatWindow } from "@/components/ChatWindow";
import { Sidebar } from "@/components/Sidebar";

export default function Page() {
  return (
    <div className="flex h-dvh overflow-hidden">
      <Sidebar />
      <ChatWindow />
    </div>
  );
}
