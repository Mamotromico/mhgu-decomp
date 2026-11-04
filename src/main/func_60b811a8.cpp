#include <cstdint>

struct Root;

struct Node {
    uint8_t pad0[0x4];
    uint32_t key;
    uint8_t pad1[0xc - 0x8];
};

struct Holder {
    uint8_t pad0[0x7c];
    uint32_t count;
    uint8_t pad1[0xf4 - 0x80];
    Node *head;
};

extern "C" Node *func_60b811a8(Root *r, uint32_t key)
{
    Holder *h = *reinterpret_cast<Holder **>(reinterpret_cast<uint8_t *>(r) + 0x64);
    Node *p = h->head;
    uint32_t n = h->count;
    if (n == 0 || p == nullptr)
        return nullptr;
    uint32_t i = 0;
    do {
        if (p->key == key)
            return p;
        i++;
        p = reinterpret_cast<Node *>(reinterpret_cast<uint8_t *>(p) + 0xc);
    } while (i < n);
    return nullptr;
}