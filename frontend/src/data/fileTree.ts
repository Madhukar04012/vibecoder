export type FileNode = {
  id: string;
  name: string;
  type: "file" | "folder";
  children?: FileNode[];
  path: string;
};

export const fileTree: FileNode[] = [
  {
    id: "app",
    name: "app",
    type: "folder",
    path: "app",
    children: [
      {
        id: "frontend",
        name: "frontend",
        type: "folder",
        path: "app/frontend",
        children: [
          {
            id: "main",
            name: "main.tsx",
            type: "file",
            path: "app/frontend/main.tsx",
          },
        ],
      },
    ],
  },
];
