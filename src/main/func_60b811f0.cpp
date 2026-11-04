#include <stdint.h>

struct Node {
    uint8_t pad0[0x4];
    uint32_t key;
    uint8_t pad8[0x4];
};

struct List {
    uint8_t pad0[0x80];
    uint32_t count;
    uint8_t pad84[0xf8 - 0x84];
    struct Node *head;
};

struct Outer {
    uint8_t pad0[0x64];
    struct List *list;
};

extern "C" void *func_60b811f0(struct Outer *o, uint32_t v)
{
    struct List *l = o->list;
    if (l->head == 0)
        return 0;
    uint32_t n = l->count;
    if (n == 0)
        return 0;
    struct Node *p = l->head;
    uint32_t i = 0;
    do {
        if (p->key == v)
            return p;
        i++;
        p = (struct Node *)((uint8_t *)p + 0xc);
    } while (i < n);
    return 0;
}