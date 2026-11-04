#include <cstdint>

struct Inner {
    uint8_t pad0[1];      // +0x00
    uint8_t f1;           // +0x01
    uint16_t f2;          // +0x02
    uint8_t pad4[0xc - 0x4]; // +0x04 .. +0x0b
    uint32_t f12;         // +0x0c
    uint32_t f16;         // +0x10
    uint32_t f20;         // +0x14
    uint8_t f24;          // +0x18
    uint8_t pad25[0x1c - 0x19];
};

struct Outer {
    uint8_t pad0[0x4 - 0x0]; // +0x00 .. +0x03
    Inner *inner;            // +0x04
    uint8_t pad8[0xa - 0x8]; // +0x08 .. +0x09
    uint8_t fA;              // +0x0a
    uint8_t padB[0xe - 0xb]; // +0x0b .. +0x0d
    uint16_t fE;             // +0x0e
    uint8_t pad10[0x14 - 0x10]; // +0x10 .. +0x13
    uint32_t f14;            // +0x14
    uint32_t f18;            // +0x18
    uint32_t f1C;            // +0x1c
    uint8_t f20;             // +0x20
};

extern "C" int func_61364c94(Outer *o) {
    Inner *i = o->inner;
    o->fA = i->f1;
    o->fE = i->f2;
    o->f14 = i->f12;
    o->f18 = i->f16;
    o->f1C = i->f20;
    o->f20 = i->f24;
    return 1;
}