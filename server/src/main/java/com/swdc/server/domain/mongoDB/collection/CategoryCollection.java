package com.swdc.server.domain.mongoDB.collection;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.springframework.data.annotation.Id;


@Getter
@Setter
@NoArgsConstructor
public class CategoryCollection {
    @Id
    private Integer id;
    private String category_name;
}
