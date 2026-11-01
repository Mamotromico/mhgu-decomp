extern "C" {

struct node {
    char pad0[4];
    node* next;       // +0x4
    char pad1[4];
    unsigned int key; // +0x10
};

struct list {
    char pad0[8];
    node head;        // at +0x8, head.next at +0xc
};

void* func_613a77c0(list* l, unsigned int key)
{
    char* sentinel = (char*)l + 0x8;
    char* n = *(char**)((char*)l + 0xc);
    while (n != sentinel) {
        if (*(unsigned int*)(n + 0x10) == key)
            return n + 0x8;
        n = *(char**)(n + 0x4);
    }
    return 0;
}

}