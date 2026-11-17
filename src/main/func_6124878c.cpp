extern "C" {

struct S {
    char pad0[0x58];
    // field at 0x58 passed to func_6122b194
    char pad1[0x74 - 0x58 - 0x0]; // ensure field at 0x74
};

// Actually we need precise layout: 0x58 used as pointer arg, 0x74 a 32-bit field.
// Define struct with correct offsets.
struct S2 {
    char pad[0x58];
    unsigned field58; // used merely as base? we pass address of it
    char pad2[0x74 - 0x5c];
    unsigned field74;
};

// But the function passes (r5 + 0x58) as r0 to callee, and stores r2 at (r5+0x74).
// So define a struct with a byte array and access at exact offsets.

void func_6122b194(void *p);

struct T {
    char pad[0x78]; // enough
};

void func_6124878c(T *self, void *a1, unsigned v) {
    func_6122b194((char*)self + 0x58);
    *(unsigned *)((char*)self + 0x74) = v;
}

}