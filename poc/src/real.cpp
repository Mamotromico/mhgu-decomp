// 32-byte struct copy: a Blob sitting at Holder+0x30, copied by value from src.
typedef unsigned int u32;

struct Blob   { u32 w[8]; };                 // 32 bytes
struct Holder { char pad[0x30]; Blob b; };   // Blob sits at +0x30

extern "C" void copy_blob(Holder *h, const Blob *src) {
    h->b = *src;
}
