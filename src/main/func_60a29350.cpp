extern "C" struct S {
    char pad0[0x14];
    S* field_14;
    char pad18[0x4];
    unsigned char field_1c;
};

extern "C" void func_60a29350(S* s) {
    S* next = *reinterpret_cast<S**>(reinterpret_cast<char*>(s->field_14) + 0x18);
    s->field_14 = next;
    if (next == nullptr) {
        *reinterpret_cast<unsigned char*>(reinterpret_cast<char*>(s) + 0x1c) = 1;
    }
}