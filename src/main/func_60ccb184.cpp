extern "C" {

struct Node {
    unsigned int field0;
    char pad1[0x18 - 0x4];
    Node* next;          // +0x18
    char pad2[0x20 - 0x1C];
    unsigned int field20; // +0x20
};

void func_60ccb184(Node** head)
{
    Node* p = *head;
    if (p == 0)
        return;
    unsigned int v = 1;
    do {
        p->field20 = v;
        v += 1;
        p = p->next;
    } while (p != 0);
}

}