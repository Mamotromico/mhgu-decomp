struct S_603c2f28 {
    char pad0[0xd54];
    unsigned char field_0xd54;
};

extern "C" void* func_603c2f28(S_603c2f28* p) {
    return p->field_0xd54 ? (void*)((char*)p + 0x1fc) : 0;
}