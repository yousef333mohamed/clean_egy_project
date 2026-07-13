"use client";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  activatePrompt,
  archivePrompt,
  createPrompt,
  getPrompts,
  getPromptVersions,
} from "@/lib/api/prompts";
import { userErrorMessage } from "@/lib/api/errors";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { StatePanel } from "@/components/shared/state-panel";
import { Skeleton } from "@/components/ui/skeleton";
export function PromptWorkspace() {
  const prompts = useQuery({
    queryKey: ["prompts"],
    queryFn: ({ signal }) => getPrompts(signal),
    staleTime: 30_000,
  });
  const [selected, setSelected] = useState<string>();
  const versions = useQuery({
    queryKey: ["prompt-versions", selected],
    queryFn: ({ signal }) => getPromptVersions(selected!, signal),
    enabled: Boolean(selected),
    staleTime: 15_000,
  });
  const client = useQueryClient();
  const mutation = useMutation({
    mutationFn: ({
      action,
      key,
      version,
      content,
    }: {
      action: "activate" | "archive" | "create";
      key: string;
      version: string;
      content?: string;
    }) =>
      action === "activate"
        ? activatePrompt(key, version)
        : action === "archive"
          ? archivePrompt(key, version)
          : createPrompt(key, {
              version,
              content,
              description: "Created from development dashboard",
            }),
    onSuccess: () => {
      toast.success("Prompt version updated");
      void client.invalidateQueries({ queryKey: ["prompts"] });
      void client.invalidateQueries({ queryKey: ["prompt-versions"] });
    },
    onError: (e) => toast.error(userErrorMessage(e)),
  });
  if (prompts.isPending) return <Skeleton className="h-64" />;
  if (prompts.isError)
    return (
      <StatePanel
        kind="error"
        title="Prompt administration unavailable"
        description="This API must be protected before production and may be disabled."
      />
    );
  return (
    <div className="grid gap-5 lg:grid-cols-[320px_1fr]">
      <Card>
        <CardHeader>
          <CardTitle>Prompt keys</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {prompts.data.map((prompt) => (
            <button
              key={prompt.prompt_key}
              onClick={() => setSelected(prompt.prompt_key)}
              className="hover:bg-muted flex w-full items-center justify-between rounded-lg border p-3 text-start"
            >
              <span>{prompt.prompt_key}</span>
              <Badge>{prompt.active_version ?? "No active version"}</Badge>
            </button>
          ))}
        </CardContent>
      </Card>
      <div>
        {!selected ? (
          <StatePanel
            title="Select a prompt"
            description="Prompt content is not returned by listing APIs."
          />
        ) : versions.isPending ? (
          <Skeleton className="h-64" />
        ) : (
          <div className="space-y-3">
            <NewPromptDialog
              promptKey={selected}
              pending={mutation.isPending}
              onCreate={(version, content) =>
                mutation.mutate({
                  action: "create",
                  key: selected,
                  version,
                  content,
                })
              }
            />
            {versions.data?.map((version) => (
              <Card key={version.id}>
                <CardHeader>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <CardTitle>
                      {version.prompt_key} · {version.version}
                    </CardTitle>
                    <Badge>{version.status}</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <dl className="grid gap-2 text-sm sm:grid-cols-2">
                    <div>
                      <dt className="text-muted-foreground">Content hash</dt>
                      <dd>
                        <code>{version.content_hash}</code>
                      </dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">Activated</dt>
                      <dd>{version.activated_at ?? "Never"}</dd>
                    </div>
                  </dl>
                  <div className="mt-4 flex gap-2">
                    {version.status !== "ACTIVE" &&
                      version.status !== "ARCHIVED" && (
                        <ConfirmButton
                          label="Activate"
                          warning="Changing an active prompt can affect every GenAI response. Run evaluations before activation."
                          onConfirm={() =>
                            mutation.mutate({
                              action: "activate",
                              key: selected,
                              version: version.version,
                            })
                          }
                        />
                      )}
                    {version.status !== "ACTIVE" &&
                      version.status !== "ARCHIVED" && (
                        <Button
                          variant="outline"
                          onClick={() =>
                            mutation.mutate({
                              action: "archive",
                              key: selected,
                              version: version.version,
                            })
                          }
                        >
                          Archive
                        </Button>
                      )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
function ConfirmButton({
  label,
  warning,
  onConfirm,
}: {
  label: string;
  warning: string;
  onConfirm: () => void;
}) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>{label}</Button>
      </DialogTrigger>
      <DialogContent title="Confirm prompt activation" description={warning}>
        <Button onClick={onConfirm}>Confirm activation</Button>
      </DialogContent>
    </Dialog>
  );
}
function NewPromptDialog({
  promptKey,
  pending,
  onCreate,
}: {
  promptKey: string;
  pending: boolean;
  onCreate: (version: string, content: string) => void;
}) {
  const [version, setVersion] = useState("");
  const [content, setContent] = useState("");
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Create draft for {promptKey}</Button>
      </DialogTrigger>
      <DialogContent
        title="Create prompt draft"
        description="The new version remains a draft and will not be activated automatically."
      >
        <div className="space-y-3">
          <label className="block text-sm font-medium">
            Semantic version
            <Input
              value={version}
              onChange={(e) => setVersion(e.target.value)}
              placeholder="1.1.0"
            />
          </label>
          <label className="block text-sm font-medium">
            Prompt content
            <Textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              maxLength={100000}
              className="min-h-52"
            />
          </label>
          <Button
            disabled={pending || !version || !content.trim()}
            onClick={() => onCreate(version, content)}
          >
            Create draft
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
