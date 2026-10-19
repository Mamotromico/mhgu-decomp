struct Outer_602a1bb0;

typedef int (*Fn_602a1bb0)(Outer_602a1bb0*, int);

struct Inner_602a1bb0 {
    char pad_0[0x25c];
    Fn_602a1bb0 fn_25c;
};

struct Outer_602a1bb0 {
    Inner_602a1bb0* inner;
};

extern "C" int func_602a1bb0(Outer_602a1bb0* self) {
    return self->inner->fn_25c(self, 8);
}