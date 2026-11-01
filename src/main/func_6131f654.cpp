extern "C" {

struct Node {
    char pad0[0x4];
    Node* next;
    char pad8[0x2c - 0x8];
    int key;
};

struct List {
    char pad0[0x8];
    Node head;
};

void* func_6131f654(List* list, int key) {
    Node* sentinel = (Node*)((char*)list + 0x8);
    Node* n = *(Node**)((char*)list + 0xc);
    while (n != sentinel) {
        if (*(int*)((char*)n + 0x2c) == key) {
            return (char*)n + 0x8;
        }
        n = *(Node**)((char*)n + 0x4);
    }
    return 0;
}

}