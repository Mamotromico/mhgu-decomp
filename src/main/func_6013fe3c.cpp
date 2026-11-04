#include <stdint.h>

struct Entry {
    uint8_t pad0[0x4];
    uint8_t field4;
    uint8_t field5;
    uint16_t field6;
};

struct Table {
    uint8_t pad0[0x208];
    Entry *entries[0x15];
};

extern "C" Entry *func_6013fe3c(Table *table, uint8_t a, uint16_t b, uint8_t c)
{
    for (unsigned int i = 0; i < 0x15; ++i) {
        Entry *e = table->entries[i];
        if (e == 0)
            continue;
        if (e->field5 != a)
            continue;
        if (e->field6 != b)
            continue;
        if (e->field4 != c)
            continue;
        return e;
    }
    return 0;
}