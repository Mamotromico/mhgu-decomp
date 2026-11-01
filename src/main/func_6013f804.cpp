extern "C" {
struct S1;

struct S0 {
    char pad00[0x20];
    S1* field20;          // +0x20
    char pad24[0x18];
    S1* field3c;          // +0x3c
};

struct S1 {
    void** vtable;        // +0x00
    char pad04[0x38];
    int  field3c;         // +0x3c
    char pad40[0x24];
    int  field64;         // +0x64
};

int func_6013f804(S0* self) {
    if (self->field3c->field64 != 0) {
        S1* p = self->field20;
        if (p != 0) {
            void** vt = *(void***)p;
            int (*fn)(S1*) = (int (*)(S1*))vt[15]; // 0x3c / 4
            return fn(p);
        }
    }
    return 0;
}
}