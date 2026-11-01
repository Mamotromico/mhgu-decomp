struct Node {
    Node* next;               // +0x00
    unsigned char pad[0x28 - 4];
    unsigned char field28;    // +0x28
};

extern "C" Node* func_60a43cb0(Node* p, int n)
{
    if (!p)
        return 0;
    int count = 0;
    while (p) {
        if (p->field28 == 0xb) {
            if (count == n)
                return p;
            ++count;
        }
        p = p->next;
    }
    return 0;
}