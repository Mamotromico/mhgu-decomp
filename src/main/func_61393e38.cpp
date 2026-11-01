extern "C" void func_61393e38(char *obj);

struct Node {
    char pad0[0x4];
    Node *next;         // +0x04
    char pad1[0x8];
    Node *prev;         // +0x0c
    char pad2[0x5];
    unsigned char flag; // +0x10
};

extern "C" void func_61393e38(char *obj)
{
    Node *head = (Node *)(obj + 0x8);
    Node *cur = *(Node **)(obj + 0xc);
    if (cur == head)
        return;
    do {
        *(unsigned char *)((char *)cur + 0x10) = 0;
        cur = *(Node **)((char *)cur + 0x4);
    } while (cur != head);
}